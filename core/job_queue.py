"""Durable jobs with atomic claims and bounded retry backoff."""
import time
import uuid
from .database import connect

def setup(path):
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS background_jobs (
            id INTEGER PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL,
            scope TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0, available REAL NOT NULL,
            lease TEXT, lease_until REAL NOT NULL DEFAULT 0)""")

def enqueue(path,kind,payload,scope):
    setup(path)
    with connect(path) as db:
        return db.execute("INSERT INTO background_jobs(kind,payload,scope,available) VALUES (?,?,?,?)",
                          (kind,payload,scope,time.time())).lastrowid

def claim(path,kind,scope):
    setup(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        t=time.time()
        row=db.execute("""SELECT * FROM background_jobs WHERE kind=? AND scope=?
            AND ((status='pending' AND available<=?) OR (status='running' AND lease_until<=?))
            ORDER BY id LIMIT 1""",(kind,scope,t,t)).fetchone()
        if row is None:
            return None
        token=uuid.uuid4().hex
        db.execute("UPDATE background_jobs SET status='running',attempts=attempts+1,lease=?,lease_until=? WHERE id=?",
                   (token,t+600,row["id"]))
        return {**dict(row),"lease":token,"attempts":row["attempts"]+1}

def finish(path,job,success):
    with connect(path) as db:
        status="done" if success else "pending"
        delay=0 if success else min(3600,2**min(job["attempts"],12))
        return db.execute("""UPDATE background_jobs SET status=?,available=?,lease=NULL,lease_until=0,
            payload=CASE WHEN ?='done' THEN '' ELSE payload END
            WHERE id=? AND lease=? AND status='running'""",
            (status,time.time()+delay,status,job["id"],job["lease"])).rowcount==1
