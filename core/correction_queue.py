"""Local correction queue; resolution of a signal is not proof of truth."""
import json
from .database import DB_PATH,connect,now

def sync(db,records):
    db.execute("""CREATE TABLE IF NOT EXISTS correction_tasks (
        fact_id INTEGER PRIMARY KEY, issues TEXT NOT NULL,
        status TEXT NOT NULL, updated TEXT NOT NULL)""")
    active={r["id"]:sorted(r["issues"]) for r in records if r["issues"]}
    for row in db.execute("SELECT fact_id FROM correction_tasks WHERE status='open'").fetchall():
        if row[0] not in active:
            db.execute("UPDATE correction_tasks SET status='signal_cleared',updated=? WHERE fact_id=?",(now(),row[0]))
    for fid,issues in active.items():
        db.execute("""INSERT INTO correction_tasks VALUES (?,?,'open',?)
            ON CONFLICT(fact_id) DO UPDATE SET issues=excluded.issues,status='open',updated=excluded.updated
            WHERE correction_tasks.issues!=excluded.issues OR correction_tasks.status!='open'""",
            (fid,json.dumps(issues),now()))
    return len(active)

def recent(path=DB_PATH):
    with connect(path) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='correction_tasks'").fetchone():
            return []
        return [{"fact_id":r["fact_id"],"subject":r["subject"],"predicate":r["predicate"],
                 "issues":json.loads(r["issues"]),"status":"awaiting_evidence",
                 "next_test":"Seek independent corroboration or a counterexample; do not automatically confirm.",
                 "factual_promotion_authorized":False}
                for r in db.execute("""SELECT t.*,k.subject,k.predicate FROM correction_tasks t
                    JOIN knowledge_versions k ON k.id=t.fact_id
                    WHERE t.status='open' AND k.status='current' ORDER BY t.updated,t.fact_id LIMIT 10""")]
