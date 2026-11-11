"""Background File System Observer for Claude and Antigravity."""
import os
import time
from pathlib import Path
from typing import Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from omni_context.db import init_db
from omni_context.parsers.claude import parse_claude_jsonl
from omni_context.parsers.antigravity import parse_antigravity_transcript

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
ANTIGRAVITY_BRAIN_DIR = Path.home() / ".gemini" / "antigravity" / "brain"

class LogEventHandler(FileSystemEventHandler):
    def __init__(self, db_path: Optional[Path] = None):
        super().__init__()
        self.db_path = db_path

    def on_modified(self, event):
        if event.is_directory:
            return
        self.process_file(event.src_path)

    def on_created(self, event):
        if event.is_directory:
            return
        self.process_file(event.src_path)

    def process_file(self, file_path_str: str):
        path = Path(file_path_str)
        if not path.name.endswith(".jsonl"):
            return

        try:
            # Check if this is a Claude session log
            if str(CLAUDE_PROJECTS_DIR).lower() in str(path).lower():
                parse_claude_jsonl(path, db_path=self.db_path)
            # Check if this is an Antigravity transcript
            elif str(ANTIGRAVITY_BRAIN_DIR).lower() in str(path).lower() and path.name == "transcript.jsonl":
                parse_antigravity_transcript(path, db_path=self.db_path)
        except Exception as e:
            # Fail softly in background daemon
            pass

def sync_all_existing(db_path: Optional[Path] = None) -> int:
    """Scan and index all existing session logs across Claude and Antigravity."""
    init_db(db_path)
    total_events = 0

    # 1. Scan Claude projects
    if CLAUDE_PROJECTS_DIR.exists():
        for jsonl_file in CLAUDE_PROJECTS_DIR.glob("*/*.jsonl"):
            try:
                total_events += parse_claude_jsonl(jsonl_file, db_path=db_path)
            except Exception:
                pass

    # 2. Scan Antigravity sessions
    if ANTIGRAVITY_BRAIN_DIR.exists():
        for transcript_file in ANTIGRAVITY_BRAIN_DIR.glob("*/.system_generated/logs/transcript.jsonl"):
            try:
                total_events += parse_antigravity_transcript(transcript_file, db_path=db_path)
            except Exception:
                pass

    return total_events

def start_watching(db_path: Optional[Path] = None):
    """Start continuous filesystem watcher."""
    init_db(db_path)
    sync_all_existing(db_path)

    event_handler = LogEventHandler(db_path=db_path)
    observer = Observer()

    if CLAUDE_PROJECTS_DIR.exists():
        observer.schedule(event_handler, str(CLAUDE_PROJECTS_DIR), recursive=True)
    if ANTIGRAVITY_BRAIN_DIR.exists():
        observer.schedule(event_handler, str(ANTIGRAVITY_BRAIN_DIR), recursive=True)

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
