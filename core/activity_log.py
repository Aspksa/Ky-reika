"""Bounded operational event history; no dialogue text or credentials."""
from .database import now

def append(db,kind,subject,status,delta=None):
    db.execute("""CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT NOT NULL,
        kind TEXT NOT NULL, subject TEXT NOT NULL, status TEXT NOT NULL, delta INTEGER)""")
    db.execute("INSERT INTO activity_log(created,kind,subject,status,delta) VALUES (?,?,?,?,?)",(now(),kind,subject,status,delta))
    db.execute("DELETE FROM activity_log WHERE id <= (SELECT max(id)-10000 FROM activity_log)")

def recent(db,limit=100):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='activity_log' AND type='table'").fetchone():
        return []
    return [dict(r) for r in db.execute("SELECT * FROM activity_log ORDER BY id DESC LIMIT ?",(max(1,min(500,limit)),))]
