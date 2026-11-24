"""Internal research lifecycle. A model review is not proof."""
from .database import DB_PATH, connect, now
from .research import setup as init

def refresh(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS research_goals (
            root TEXT NOT NULL, revision INTEGER NOT NULL, question TEXT NOT NULL,
            priority REAL NOT NULL, status TEXT NOT NULL, updated TEXT NOT NULL,
            PRIMARY KEY(root,revision))""")
        db.execute("BEGIN IMMEDIATE")
        db.execute("""UPDATE research_goals SET status='superseded',updated=?
            WHERE status!='superseded' AND NOT EXISTS (
            SELECT 1 FROM research_agenda a WHERE a.root=research_goals.root
            AND a.revision=research_goals.revision)""",(now(),))
        db.execute("""INSERT INTO research_goals SELECT root,revision,question,priority,'queued',?
            FROM research_agenda WHERE 1
            ON CONFLICT(root,revision) DO UPDATE SET priority=excluded.priority,question=excluded.question,
            status=CASE WHEN research_goals.status='superseded' THEN 'queued' ELSE research_goals.status END""",(now(),))
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='background_reviews'").fetchone():
            db.execute("""UPDATE research_goals SET status=CASE
                (SELECT b.status FROM background_reviews b WHERE b.root=research_goals.root AND b.revision=research_goals.revision)
                WHEN 'unverified' THEN 'awaiting_evidence' WHEN 'failed' THEN 'review_failed'
                WHEN 'reserved' THEN 'review_started' ELSE 'queued' END,updated=?
                WHERE status!='superseded'""",(now(),))

def current(path=DB_PATH):
    refresh(path)
    with connect(path) as db:
        return [dict(r) for r in db.execute("""SELECT root,revision,question,priority,status FROM research_goals
            WHERE status!='superseded' ORDER BY CASE status WHEN 'queued' THEN 0 ELSE 1 END,priority DESC,root LIMIT 10""")]
