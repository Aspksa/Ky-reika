"""Persistent intentions; recording a plan never authorizes external execution."""
from datetime import datetime, timezone
from .database import DB_PATH, connect, initialize, now

def setup(path=DB_PATH):
    initialize(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS intentions (
            id INTEGER PRIMARY KEY, description TEXT NOT NULL,
            source_memory INTEGER REFERENCES memories(id),
            priority INTEGER NOT NULL CHECK(priority BETWEEN 1 AND 5),
            due TEXT, status TEXT NOT NULL CHECK(status IN ('pending','active','completed','cancelled')),
            created TEXT NOT NULL, updated TEXT NOT NULL)""")

def propose(description, source_memory=None, priority=3, due=None, path=DB_PATH):
    if not description.strip() or not isinstance(priority,int) or not 1<=priority<=5:
        raise ValueError("Invalid intention")
    if due is not None:
        dt=datetime.fromisoformat(due)
        if dt.tzinfo is None:
            raise ValueError("Deadline must include timezone")
        due=dt.astimezone(timezone.utc).isoformat()
    setup(path)
    with connect(path) as db:
        return db.execute("""INSERT INTO intentions
            (description,source_memory,priority,due,status,created,updated)
            VALUES (?,?,?,?,'pending',?,?)""",
            (description.strip(),source_memory,priority,due,now(),now())).lastrowid

def transition(intent_id,status,path=DB_PATH):
    allowed={"active":("pending",),"completed":("active",),"cancelled":("pending","active")}
    if status not in allowed:
        raise ValueError("Invalid target state")
    setup(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        row=db.execute("SELECT status FROM intentions WHERE id=?",(intent_id,)).fetchone()
        if not row or row["status"] not in allowed[status]:
            raise ValueError("Invalid transition")
        db.execute("UPDATE intentions SET status=?,updated=? WHERE id=?",(status,now(),intent_id))

def upcoming(path=DB_PATH,limit=10):
    setup(path)
    with connect(path) as db:
        return [dict(r) for r in db.execute("""SELECT *,
            CASE WHEN due IS NOT NULL AND due<=? THEN 1 ELSE 0 END AS due_now
            FROM intentions WHERE status='active'
            ORDER BY due_now DESC,priority DESC,due IS NULL,due,id LIMIT ?""",
            (now(),max(1,min(100,int(limit)))))]

def pending(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        return [dict(r) for r in db.execute("SELECT * FROM intentions WHERE status='pending' ORDER BY id DESC LIMIT 100")]
