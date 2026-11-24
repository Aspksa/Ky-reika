"""Prospective research ledger; observed matches do not prove general laws."""
import json
from .database import DB_PATH,connect,now
from .knowledge import setup
from .creative_intelligence import generate

def refresh(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""CREATE TABLE IF NOT EXISTS discovery_predictions (
            candidate TEXT PRIMARY KEY, sources TEXT NOT NULL, cutoff INTEGER NOT NULL,
            created TEXT NOT NULL)""")
        facts=[dict(r) for r in db.execute("SELECT id,subject,predicate,value FROM knowledge_versions WHERE status='current' ORDER BY id DESC")]
        cutoff=db.execute("SELECT coalesce(max(id),0) FROM knowledge_versions").fetchone()[0]
        existing={(r["subject"],r["predicate"]) for r in facts}
        for idea in generate(facts[:2000]):
            if tuple(idea["candidate"][:2]) in existing:
                continue
            db.execute("INSERT OR IGNORE INTO discovery_predictions VALUES (?,?,?,?)",
                (json.dumps(idea["candidate"],ensure_ascii=False),json.dumps(idea["source_ids"]),cutoff,now()))

def recent(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='discovery_predictions'").fetchone():
            return []
        facts=[dict(r) for r in db.execute("SELECT id,subject,predicate,value FROM knowledge_versions WHERE status='current'")]
        current={r["id"] for r in facts}
        by_key={(r["subject"],r["predicate"]):r for r in facts}
        result=[]
        for row in db.execute("SELECT * FROM discovery_predictions ORDER BY created DESC,candidate LIMIT 100"):
            candidate=json.loads(row["candidate"])
            sources=json.loads(row["sources"])
            observed=by_key.get(tuple(candidate[:2]))
            status="awaiting_evidence"
            if not set(sources)<=current:
                status="premises_superseded"
            elif observed and observed["id"]>row["cutoff"]:
                status="observed_match" if observed["value"]==candidate[2] else "observed_counterexample"
            elif observed:
                status="preexisting_observation"
            result.append({"candidate":candidate,"sources":sources,"status":status,
                "observation_id":observed["id"] if observed else None,
                "limitation":"Later record ID is not proof of independent observation or causality."})
        return result[:10]
