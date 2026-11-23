"""SQLite storage for Kyūreika. Standard library only."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / 'data' / 'kyureika.sqlite3'

def now():
    return datetime.now(timezone.utc).isoformat()

@contextmanager
def connect(path=DB_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA journal_mode=WAL')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def initialize(path=DB_PATH):
    with connect(path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
        INSERT OR IGNORE INTO schema_version(version) VALUES (1);
        CREATE TABLE IF NOT EXISTS personality (
            trait TEXT PRIMARY KEY, score INTEGER NOT NULL CHECK(score BETWEEN 0 AND 100)
        );
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'general',
            importance INTEGER NOT NULL DEFAULT 50 CHECK(importance BETWEEN 0 AND 100),
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS emotional_state (
            id INTEGER PRIMARY KEY CHECK(id=1),
            mood TEXT NOT NULL DEFAULT 'calm',
            trust INTEGER NOT NULL DEFAULT 50 CHECK(trust BETWEEN 0 AND 100),
            affection INTEGER NOT NULL DEFAULT 70 CHECK(affection BETWEEN 0 AND 100),
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT NOT NULL
        );
        """)
        db.executemany('INSERT OR IGNORE INTO personality(trait,score) VALUES (?,?)', TRAITS.items())
        db.execute("INSERT OR IGNORE INTO emotional_state(id,mood,trust,affection,updated_at) VALUES (1,'calm',50,70,?)", (now(),))

TRAITS = {
    'authority': 98, 'pride': 96, 'intelligence': 100, 'strictness': 92,
    'independence': 95, 'loyalty': 100, 'tenderness': 94,
    'jealousy': 65, 'playfulness': 79, 'cruelty': 24,
}

def add_memory(content, category='general', importance=50, path=DB_PATH):
    if not content.strip():
        raise ValueError('Memory content cannot be empty')
    with connect(path) as db:
        cur = db.execute('INSERT INTO memories(content,category,importance,created_at) VALUES (?,?,?,?)', (content,category,importance,now()))
        return cur.lastrowid

def list_memories(limit=20, path=DB_PATH):
    with connect(path) as db:
        return [dict(r) for r in db.execute('SELECT * FROM memories ORDER BY importance DESC,id DESC LIMIT ?', (limit,))]

def add_message(role, content, path=DB_PATH):
    with connect(path) as db:
        cur = db.execute('INSERT INTO messages(role,content,created_at) VALUES (?,?,?)', (role,content,now()))
        return cur.lastrowid

def recent_messages(limit=20, path=DB_PATH):
    with connect(path) as db:
        return [dict(r) for r in db.execute('SELECT * FROM (SELECT * FROM messages ORDER BY id DESC LIMIT ?) ORDER BY id', (limit,))]

def get_state(path=DB_PATH):
    with connect(path) as db:
        return dict(db.execute('SELECT * FROM emotional_state WHERE id=1').fetchone())

def set_state(mood, trust, affection, path=DB_PATH):
    if not (0 <= trust <= 100 and 0 <= affection <= 100):
        raise ValueError('Emotional scores must be between 0 and 100')
    with connect(path) as db:
        db.execute('UPDATE emotional_state SET mood=?,trust=?,affection=?,updated_at=? WHERE id=1', (mood,trust,affection,now()))
