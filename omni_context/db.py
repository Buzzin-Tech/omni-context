import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

DEFAULT_DB_DIR = Path.home() / ".omni-context"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "context.db"

def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    target_path = db_path or DEFAULT_DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

def init_db(db_path: Optional[Path] = None):
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        agent TEXT NOT NULL,
        project_name TEXT,
        project_path TEXT,
        started_at TEXT,
        last_active_at TEXT,
        summary TEXT
    );

    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        agent TEXT NOT NULL,
        event_type TEXT NOT NULL,
        timestamp TEXT,
        content TEXT,
        metadata_json TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );

    CREATE TABLE IF NOT EXISTS file_touches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        agent TEXT NOT NULL,
        file_path TEXT NOT NULL,
        action TEXT NOT NULL,
        timestamp TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );

    CREATE TABLE IF NOT EXISTS ui_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        agent TEXT NOT NULL,
        project_name TEXT,
        component_name TEXT,
        tech_stack TEXT,
        code_snippet TEXT,
        style_summary TEXT,
        timestamp TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );

    CREATE TABLE IF NOT EXISTS file_offsets (
        file_path TEXT PRIMARY KEY,
        last_offset INTEGER DEFAULT 0,
        last_mtime REAL DEFAULT 0
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS events_fts USING fts5(
        session_id UNINDEXED,
        agent,
        content,
        tokenize='porter unicode61'
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS ui_fts USING fts5(
        session_id UNINDEXED,
        agent,
        project_name,
        component_name,
        style_summary,
        code_snippet,
        tokenize='porter unicode61'
    );
    """)
    conn.commit()
    conn.close()

def save_session(session_id: str, agent: str, project_name: str = "", project_path: str = "", 
                 started_at: str = "", last_active_at: str = "", summary: str = "", 
                 conn: Optional[sqlite3.Connection] = None, db_path: Optional[Path] = None):
    close_after = False
    if conn is None:
        conn = get_db_connection(db_path)
        close_after = True

    conn.execute("""
    INSERT INTO sessions (session_id, agent, project_name, project_path, started_at, last_active_at, summary)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(session_id) DO UPDATE SET
        last_active_at = CASE WHEN excluded.last_active_at != '' THEN excluded.last_active_at ELSE sessions.last_active_at END,
        summary = CASE WHEN excluded.summary != '' THEN excluded.summary ELSE sessions.summary END,
        project_name = CASE WHEN excluded.project_name != '' THEN excluded.project_name ELSE sessions.project_name END,
        project_path = CASE WHEN excluded.project_path != '' THEN excluded.project_path ELSE sessions.project_path END
    """, (session_id, agent, project_name, project_path, started_at, last_active_at, summary))

    if close_after:
        conn.commit()
        conn.close()

def save_event(session_id: str, agent: str, event_type: str, content: str, 
               timestamp: str = "", metadata: Optional[Dict[str, Any]] = None, 
               conn: Optional[sqlite3.Connection] = None, db_path: Optional[Path] = None) -> int:
    close_after = False
    if conn is None:
        conn = get_db_connection(db_path)
        close_after = True

    meta_json = json.dumps(metadata or {})
    cur = conn.execute("""
    INSERT INTO events (session_id, agent, event_type, timestamp, content, metadata_json)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, agent, event_type, timestamp, content, meta_json))
    event_id = cur.lastrowid
    
    conn.execute("""
    INSERT INTO events_fts (session_id, agent, content)
    VALUES (?, ?, ?)
    """, (session_id, agent, content))

    if close_after:
        conn.commit()
        conn.close()
    return event_id

def save_file_touch(session_id: str, agent: str, file_path: str, action: str, timestamp: str = "", 
                    conn: Optional[sqlite3.Connection] = None, db_path: Optional[Path] = None):
    close_after = False
    if conn is None:
        conn = get_db_connection(db_path)
        close_after = True

    conn.execute("""
    INSERT INTO file_touches (session_id, agent, file_path, action, timestamp)
    VALUES (?, ?, ?, ?, ?)
    """, (session_id, agent, file_path, action, timestamp))

    if close_after:
        conn.commit()
        conn.close()

def save_ui_pattern(session_id: str, agent: str, project_name: str, component_name: str,
                    tech_stack: str, code_snippet: str, style_summary: str, timestamp: str = "", 
                    conn: Optional[sqlite3.Connection] = None, db_path: Optional[Path] = None):
    close_after = False
    if conn is None:
        conn = get_db_connection(db_path)
        close_after = True

    conn.execute("""
    INSERT INTO ui_patterns (session_id, agent, project_name, component_name, tech_stack, code_snippet, style_summary, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (session_id, agent, project_name, component_name, tech_stack, code_snippet, style_summary, timestamp))
    
    conn.execute("""
    INSERT INTO ui_fts (session_id, agent, project_name, component_name, style_summary, code_snippet)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, agent, project_name, component_name, style_summary, code_snippet))

    if close_after:
        conn.commit()
        conn.close()

def get_file_offset(file_path: str, conn: Optional[sqlite3.Connection] = None, db_path: Optional[Path] = None) -> int:
    close_after = False
    if conn is None:
        conn = get_db_connection(db_path)
        close_after = True

    row = conn.execute("SELECT last_offset FROM file_offsets WHERE file_path = ?", (file_path,)).fetchone()
    offset = row["last_offset"] if row else 0

    if close_after:
        conn.close()
    return offset

def update_file_offset(file_path: str, offset: int, mtime: float, 
                       conn: Optional[sqlite3.Connection] = None, db_path: Optional[Path] = None):
    close_after = False
    if conn is None:
        conn = get_db_connection(db_path)
        close_after = True

    conn.execute("""
    INSERT INTO file_offsets (file_path, last_offset, last_mtime)
    VALUES (?, ?, ?)
    ON CONFLICT(file_path) DO UPDATE SET
        last_offset = excluded.last_offset,
        last_mtime = excluded.last_mtime
    """, (file_path, offset, mtime))

    if close_after:
        conn.commit()
        conn.close()

def query_recent_sessions(limit: int = 10, agent: Optional[str] = None, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    if agent:
        rows = conn.execute("""
        SELECT * FROM sessions WHERE agent = ? ORDER BY last_active_at DESC LIMIT ?
        """, (agent, limit)).fetchall()
    else:
        rows = conn.execute("""
        SELECT * FROM sessions ORDER BY last_active_at DESC LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def search_events(query: str, limit: int = 10, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    # Sanitize query for FTS5
    safe_query = '"' + query.replace('"', '""') + '"'
    rows = conn.execute("""
    SELECT e.session_id, e.agent, e.event_type, e.timestamp, e.content, s.project_name
    FROM events_fts f
    JOIN events e ON e.rowid = f.rowid
    LEFT JOIN sessions s ON s.session_id = e.session_id
    WHERE events_fts MATCH ?
    ORDER BY rank
    LIMIT ?
    """, (safe_query, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def query_ui_patterns(project: Optional[str] = None, search: Optional[str] = None, limit: int = 5, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    if search:
        safe_search = '"' + search.replace('"', '""') + '"'
        rows = conn.execute("""
        SELECT u.* FROM ui_fts f
        JOIN ui_patterns u ON u.rowid = f.rowid
        WHERE ui_fts MATCH ?
        LIMIT ?
        """, (safe_search, limit)).fetchall()
    elif project:
        rows = conn.execute("""
        SELECT * FROM ui_patterns WHERE project_name LIKE ? ORDER BY timestamp DESC LIMIT ?
        """, (f"%{project}%", limit)).fetchall()
    else:
        rows = conn.execute("""
        SELECT * FROM ui_patterns ORDER BY timestamp DESC LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def query_recent_file_touches(limit: int = 15, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    rows = conn.execute("""
    SELECT f.*, s.project_name 
    FROM file_touches f
    LEFT JOIN sessions s ON s.session_id = f.session_id
    ORDER BY f.id DESC
    LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
