"""Local research agenda; no external actions or automatic rule promotion."""
import json
from .database import DB_PATH, connect, now
from .thought_tree import setup as init

def setup(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS research_agenda (
            root TEXT PRIMARY KEY REFERENCES development_thoughts(fingerprint),
            revision INTEGER NOT NULL, priority REAL NOT NULL,
            method TEXT NOT NULL, question TEXT NOT NULL, updated TEXT NOT NULL)""")

def refresh(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("DELETE FROM research_agenda WHERE root NOT IN (SELECT fingerprint FROM development_thoughts WHERE status='candidate')")
        for r in db.execute("SELECT * FROM development_thoughts WHERE status='candidate'").fetchall():
            h=json.loads(r["content"])
            if r["kind"]=="rule":
                method="counterexample_search"
                priority=.9 if h.get("counterexamples") else .8 if h.get("validation_frequency") is None else .5
                question="Which confirmed subjects test this association: "+str(h["premise"])+" -> "+str(h["conclusion"])+"?"
            elif r["kind"]=="explanation":
                method="abductive_verification"
                priority=.7
                question="Can missing conditions be verified for "+str(h["observation"])+"?"
            else:
                method="inductive_validation"
                priority=.6
                question="Does the pattern persist in new observations of "+h["predicate"]+"?"
            db.execute("""INSERT INTO research_agenda VALUES (?,?,?,?,?,?)
                ON CONFLICT(root) DO UPDATE SET revision=excluded.revision,priority=excluded.priority,
                method=excluded.method,question=excluded.question,updated=excluded.updated""",
                (r["fingerprint"],r["observations"],priority,method,question,now()))

def agenda(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        return [dict(r) for r in db.execute("""SELECT a.method,a.question,a.priority,a.revision
            FROM research_agenda a JOIN development_thoughts d ON d.fingerprint=a.root
            WHERE d.status='candidate' AND a.revision=d.observations
            ORDER BY a.priority DESC,a.root LIMIT 5""")]
