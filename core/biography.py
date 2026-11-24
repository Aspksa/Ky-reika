"""Recorded software-persona history, not invented lived experiences."""
from .database import DB_PATH, connect, now
from .cognition import setup as init, unit

def setup(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS biography_events (
            id INTEGER PRIMARY KEY, kind TEXT NOT NULL,
            description TEXT NOT NULL, source_memory INTEGER REFERENCES memories(id),
            significance REAL NOT NULL, created TEXT NOT NULL,
            UNIQUE(kind,source_memory))""")

def record(kind,description,memory_id,significance=.5,path=DB_PATH):
    if kind not in ("dialogue","milestone","reflection","decision") or not description.strip():
        raise ValueError("Invalid event")
    setup(path)
    with connect(path) as db:
        db.execute("""INSERT OR IGNORE INTO biography_events
            (kind,description,source_memory,significance,created) VALUES (?,?,?,?,?)""",
            (kind,description,memory_id,unit(significance),now()))

def timeline(path=DB_PATH,limit=12):
    setup(path)
    with connect(path) as db:
        return [dict(r) for r in db.execute("""SELECT * FROM
            (SELECT * FROM biography_events ORDER BY significance DESC,id DESC LIMIT ?)
            ORDER BY id""",(max(1,min(100,int(limit))),))]
