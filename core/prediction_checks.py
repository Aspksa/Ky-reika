"""Exact observation checks; missing evidence is not falsification."""
import json
from .database import DB_PATH, connect, now
from .theory_review import recent as reviews
from .inference import triple

def evaluate(prediction, facts, cutoff):
    subject,predicate,value=triple(prediction)
    matches=[f for f in facts if f["id"]>cutoff and
             (f["subject"],f["predicate"])==(subject,predicate)]
    return {"status":"awaiting_observation" if not matches else
            "supported_observation" if all(f["value"]==value for f in matches) else "contradicting_observation",
            "sources":[f["id"] for f in matches]}

def refresh(path=DB_PATH):
    active=reviews(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""CREATE TABLE IF NOT EXISTS prediction_checks (
            id TEXT, revision INTEGER, content TEXT NOT NULL, updated TEXT NOT NULL,
            PRIMARY KEY(id,revision))""")
        facts=[dict(r) for r in db.execute("SELECT id,subject,predicate,value FROM knowledge_versions WHERE status='current'")]
        for r in active:
            if "observable" not in r or "observation_cutoff" not in r:
                continue
            result=evaluate(r["observable"],facts,r["observation_cutoff"])
            result["observable"]=r["observable"]
            db.execute("""INSERT INTO prediction_checks VALUES (?,?,?,?)
                ON CONFLICT(id,revision) DO UPDATE SET content=excluded.content,updated=excluded.updated""",
                (r["id"],r["revision"],json.dumps(result,ensure_ascii=False),now()))

def recent(path=DB_PATH):
    active={(r["id"],r["revision"]):r for r in reviews(path)}
    with connect(path) as db:
        facts=[dict(r) for r in db.execute("SELECT id,subject,predicate,value FROM knowledge_versions WHERE status='current'")]
    return [{"id":key[0],"revision":key[1],"observable":r["observable"],
             **evaluate(r["observable"],facts,r["observation_cutoff"])}
            for key,r in active.items() if "observable" in r and "observation_cutoff" in r]
