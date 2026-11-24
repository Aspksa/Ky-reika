"""Versioned knowledge; unconfirmed observations never replace confirmed facts."""
from .database import DB_PATH, connect, initialize, now
from .cognition import unit

def setup(path=DB_PATH):
    initialize(path)
    with connect(path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS knowledge_versions (
            id INTEGER PRIMARY KEY, subject TEXT NOT NULL, predicate TEXT NOT NULL,
            value TEXT NOT NULL, source TEXT NOT NULL, confidence REAL NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending','current','superseded','rejected')),
            created TEXT NOT NULL, ended TEXT);
        CREATE UNIQUE INDEX IF NOT EXISTS knowledge_current
            ON knowledge_versions(subject,predicate) WHERE status='current';
        """)

def propose(subject,predicate,value,source,confidence=.5,path=DB_PATH):
    fields=[x.strip() for x in (subject,predicate,value,source)]
    if not all(fields):
        raise ValueError("Missing knowledge field")
    fields[0]=fields[0].casefold()
    fields[1]=fields[1].casefold()
    setup(path)
    with connect(path) as db:
        return db.execute("""INSERT INTO knowledge_versions
            (subject,predicate,value,source,confidence,status,created)
            VALUES (?,?,?,?,?,'pending',?)""",(*fields,unit(confidence),now())).lastrowid

def confirm(version_id,path=DB_PATH):
    setup(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        row=db.execute("SELECT * FROM knowledge_versions WHERE id=? AND status='pending'",(version_id,)).fetchone()
        if row is None:
            raise ValueError("No pending version")
        db.execute("UPDATE knowledge_versions SET status='superseded',ended=? WHERE subject=? AND predicate=? AND status='current'",(now(),row["subject"],row["predicate"]))
        db.execute("UPDATE knowledge_versions SET status='current' WHERE id=?",(version_id,))

def history(subject,predicate,path=DB_PATH):
    setup(path)
    with connect(path) as db:
        return [dict(r) for r in db.execute("SELECT * FROM knowledge_versions WHERE subject=? AND predicate=? ORDER BY id",(subject.strip().casefold(),predicate.strip().casefold()))]

def relevant(query,path=DB_PATH):
    from .reasoning import tokens
    terms=tokens(query)
    setup(path)
    with connect(path) as db:
        rows=[dict(r) for r in db.execute("SELECT * FROM knowledge_versions WHERE status='current'")]
    matches=[r for r in rows if terms & tokens(r["subject"]+" "+r["predicate"]+" "+r["value"])]
    return sorted(matches,key=lambda r:(r["confidence"],r["id"]),reverse=True)[:8]
