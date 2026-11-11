"""Incremental Parser for Antigravity transcript JSONL logs."""
import json
from pathlib import Path
from typing import Optional

from omni_context.db import (
    get_db_connection, save_session, save_event, save_file_touch, save_ui_pattern,
    get_file_offset, update_file_offset
)
from omni_context.ui_extractor import extract_ui_features

def parse_antigravity_transcript(transcript_path: Path, db_path: Optional[Path] = None) -> int:
    if not transcript_path.exists():
        return 0

    stat = transcript_path.stat()
    last_offset = get_file_offset(str(transcript_path), db_path=db_path)
    if stat.st_size <= last_offset:
        return 0

    session_dir = transcript_path.parent.parent.parent
    session_id = session_dir.name
    project_name = f"antigravity-{session_id[:8]}"

    conn = get_db_connection(db_path)
    events_parsed = 0
    batch_count = 0

    try:
        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(last_offset)
            
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue

                source = data.get("source", "")
                step_type = data.get("type", "")
                ts = data.get("created_at", "")
                content = data.get("content", "")
                tool_calls = data.get("tool_calls", [])

                save_session(
                    session_id=session_id,
                    agent="antigravity",
                    project_name=project_name,
                    started_at=ts,
                    last_active_at=ts,
                    conn=conn
                )

                if source == "USER_INPUT" or step_type == "USER_INPUT":
                    text = str(content).strip()
                    if text:
                        save_event(session_id, "antigravity", "prompt", text, timestamp=ts, conn=conn)
                        events_parsed += 1
                        batch_count += 1

                elif source == "MODEL" and step_type == "PLANNER_RESPONSE":
                    if content and isinstance(content, str) and content.strip():
                        save_event(session_id, "antigravity", "response", content.strip()[:1500], timestamp=ts, conn=conn)
                        events_parsed += 1
                        batch_count += 1

                    for call in tool_calls:
                        name = call.get("name", "")
                        args = call.get("args", {})
                        
                        if name in ("write_file", "edit_file"):
                            file_path = args.get("Path", "")
                            file_content = args.get("Content") or args.get("Replacement") or ""
                            action = "edit" if name == "edit_file" else "write"
                            
                            if file_path:
                                save_file_touch(session_id, "antigravity", file_path, action, timestamp=ts, conn=conn)
                                
                                ui_feat = extract_ui_features(file_path, file_content)
                                if ui_feat:
                                    save_ui_pattern(
                                        session_id=session_id,
                                        agent="antigravity",
                                        project_name=project_name,
                                        component_name=ui_feat["component_name"],
                                        tech_stack=ui_feat["tech_stack"],
                                        code_snippet=ui_feat["code_snippet"],
                                        style_summary=ui_feat["style_summary"],
                                        timestamp=ts,
                                        conn=conn
                                    )

                        elif name == "run_command":
                            cmd = args.get("CommandLine", "")
                            summary = args.get("toolSummary", "")
                            if cmd:
                                save_event(session_id, "antigravity", "tool_call", f"Cmd: {cmd} ({summary})", timestamp=ts, metadata={"tool": "run_command", "cmd": cmd}, conn=conn)
                                events_parsed += 1
                                batch_count += 1

                if batch_count >= 100:
                    conn.commit()
                    batch_count = 0

            new_offset = f.tell()
            update_file_offset(str(transcript_path), new_offset, stat.st_mtime, conn=conn)
            conn.commit()
    finally:
        conn.close()

    return events_parsed
