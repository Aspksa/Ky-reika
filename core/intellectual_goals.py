"""Persistent internal research priorities; no external actions."""
from .database import DB_PATH, connect, now
from .research_goals import refresh as init

def refresh(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS intellectual_goals (
            root TEXT PRIMARY KEY, revision INTEGER NOT NULL, question TEXT NOT NULL,
            cycles INTEGER NOT NULL, last_selected TEXT, priority REAL NOT NULL,
            status TEXT NOT NULL)""")
        db.execute("BEGIN IMMEDIATE")
        db.execute("""UPDATE intellectual_goals SET status='inactive' WHERE NOT EXISTS (
            SELECT 1 FROM research_goals g WHERE g.root=intellectual_goals.root
            AND g.status!='superseded')""")
        db.execute("""INSERT INTO intellectual_goals
            SELECT root,revision,question,1,NULL,priority,status FROM research_goals
            WHERE status!='superseded'
            ON CONFLICT(root) DO UPDATE SET
            cycles=CASE WHEN intellectual_goals.revision=excluded.revision THEN intellectual_goals.cycles+1 ELSE 1 END,
            revision=excluded.revision,question=excluded.question,priority=excluded.priority,status=excluded.status""")
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='background_reviews' AND type='table'").fetchone():
            db.execute("""UPDATE intellectual_goals SET last_selected=(
                SELECT max(b.created) FROM background_reviews b
                WHERE b.root=intellectual_goals.root AND b.revision=intellectual_goals.revision)
                WHERE status!='inactive'""")
        row=db.execute("""SELECT root FROM intellectual_goals WHERE status IN ('queued','review_failed')
            ORDER BY last_selected IS NOT NULL,last_selected,priority DESC,root LIMIT 1""").fetchone()
        return row["root"] if row else None

def current(path=DB_PATH):
    with connect(path) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='intellectual_goals' AND type='table'").fetchone():
            return []
        return [{**dict(r),"stagnation_signal":r["cycles"]>=10 and r["status"]=="awaiting_evidence",
                 "authority":"internal_research_only"} for r in db.execute("""SELECT * FROM intellectual_goals
            WHERE status!='inactive' ORDER BY last_selected DESC,priority DESC LIMIT 10""")]
