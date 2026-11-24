"""Local maintenance diagnostics with reversible historical records."""
import json
from .database import DB_PATH, connect, now
from .reflection import inspect
from .revision import audit

def refresh(path=DB_PATH):
    memory=inspect(path)
    before=audit(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS cognitive_health (
            id INTEGER PRIMARY KEY, content TEXT NOT NULL, created TEXT NOT NULL)""")
        db.execute("BEGIN IMMEDIATE")
        sources={r[0] for r in db.execute("SELECT id FROM knowledge_versions WHERE status='current'")}
        rules={r[0] for r in db.execute("SELECT id FROM inference_rules")}
        withdrawn=[]
        for row in db.execute("SELECT id,evidence FROM deduction_history WHERE withdrawn IS NULL").fetchall():
            proof=json.loads(row["evidence"])
            if not set(proof["sources"])<=sources or not set(proof["rules"])<=rules:
                db.execute("UPDATE deduction_history SET withdrawn=? WHERE id=?",(now(),row["id"]))
                withdrawn.append(row["id"])
        metrics={k:memory[k] for k in ("low_confidence","disputed_memories","pending_knowledge","potential_conflicts")}
        previous=db.execute("SELECT content FROM cognitive_health ORDER BY id DESC LIMIT 1").fetchone()
        baseline=json.loads(previous[0])["metrics"] if previous else metrics
        changes={k:metrics[k]-baseline[k] for k in metrics}
        report={"metrics":metrics,"changes":changes,"stale_before":len(before["stale_records"]),
                "withdrawn_records":withdrawn,"recommendations":memory["recommendations"],
                "status":"review_required" if any(metrics.values()) or withdrawn else "no_detected_issue",
                "limitation":"Counts are maintenance signals, not measures of intelligence."}
        db.execute("INSERT INTO cognitive_health(content,created) VALUES (?,?)",(json.dumps(report),now()))
        db.execute("DELETE FROM cognitive_health WHERE id NOT IN (SELECT id FROM cognitive_health ORDER BY id DESC LIMIT 1000)")
    return report

def latest(path=DB_PATH):
    with connect(path) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='cognitive_health'").fetchone():
            return {}
        row=db.execute("SELECT content,created FROM cognitive_health ORDER BY id DESC LIMIT 1").fetchone()
        return {"created":row["created"],**json.loads(row["content"])} if row else {}
