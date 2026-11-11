"""Incremental Parser for Claude Code session JSONL logs."""
import json
from pathlib import Path
from typing import Optional

from omni_context.db import (
    get_db_connection, save_session, save_event, save_file_touch, save_ui_pattern,
    get_file_offset, update_file_offset
)
from omni_context.ui_extractor import extract_ui_features

def clean_project_name(folder_name: str) -> str:
    parts = folder_name.split("-")
    if len(parts) > 2 and parts[0] == "C" and parts[1] == "":
        return "-".join(parts[2:])
    return folder_name

def parse_claude_jsonl(file_path: Path, db_path: Optional[Path] = None) -> int:
    if not file_path.exists():
        return 0

    stat = file_path.stat()
    last_offset = get_file_offset(str(file_path), db_path=db_path)
    if stat.st_size <= last_offset:
        return 0

    folder_name = file_path.parent.name
    project_name = clean_project_name(folder_name)
    session_id = file_path.stem

    conn = get_db_connection(db_path)
    events_parsed = 0
    batch_count = 0

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(last_offset)
            
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue

                event_type = data.get("type")
                ts = data.get("timestamp", "")
                cwd = data.get("cwd", "")
                
                save_session(
                    session_id=session_id,
                    agent="claude",
                    project_name=project_name,
                    project_path=cwd,
                    started_at=ts,
                    last_active_at=ts,
                    conn=conn
                )

                if event_type == "user":
                    message = data.get("message", {})
                    content = message.get("content", "")
                    if isinstance(content, list):
                        texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
                        prompt_text = " ".join(texts)
                    else:
                        prompt_text = str(content)

                    if prompt_text.strip():
                        save_event(session_id, "claude", "prompt", prompt_text.strip(), timestamp=ts, conn=conn)
                        events_parsed += 1
                        batch_count += 1

                elif event_type in ("ai-title", "custom-title"):
                    title = data.get("title") or data.get("content", "")
                    if title:
                        save_session(session_id=session_id, agent="claude", summary=title, last_active_at=ts, conn=conn)

                elif event_type == "assistant":
                    msg = data.get("message", {})
                    content_list = msg.get("content", [])
                    if isinstance(content_list, list):
                        for item in content_list:
                            if not isinstance(item, dict):
                                continue
                            
                            itype = item.get("type")
                            if itype == "text":
                                txt = item.get("text", "").strip()
                                if txt:
                                    save_event(session_id, "claude", "response", txt[:1500], timestamp=ts, conn=conn)
                                    events_parsed += 1
                                    batch_count += 1
                            
                            elif itype == "tool_use":
                                tool_name = item.get("name", "")
                                tool_input = item.get("input", {})
                                
                                file_path_arg = tool_input.get("path") or tool_input.get("file_path") or tool_input.get("file")
                                file_content = tool_input.get("content") or tool_input.get("file_text") or tool_input.get("text") or ""
                                
                                if file_path_arg:
                                    action = "edit" if "edit" in tool_name.lower() else "write"
                                    save_file_touch(session_id, "claude", str(file_path_arg), action, timestamp=ts, conn=conn)
                                    
                                    ui_feat = extract_ui_features(str(file_path_arg), file_content)
                                    if ui_feat:
                                        save_ui_pattern(
                                            session_id=session_id,
                                            agent="claude",
                                            project_name=project_name,
                                            component_name=ui_feat["component_name"],
                                            tech_stack=ui_feat["tech_stack"],
                                            code_snippet=ui_feat["code_snippet"],
                                            style_summary=ui_feat["style_summary"],
                                            timestamp=ts,
                                            conn=conn
                                        )

                                elif tool_name == "Bash":
                                    cmd = tool_input.get("command", "")
                                    if cmd:
                                        save_event(session_id, "claude", "tool_call", f"Bash: {cmd}", timestamp=ts, metadata={"tool": "Bash", "cmd": cmd}, conn=conn)
                                        events_parsed += 1
                                        batch_count += 1

                if batch_count >= 100:
                    conn.commit()
                    batch_count = 0

            new_offset = f.tell()
            update_file_offset(str(file_path), new_offset, stat.st_mtime, conn=conn)
            conn.commit()
    finally:
        conn.close()

    return events_parsed
