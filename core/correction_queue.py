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

def investigate(db):
    """Review one least recently investigated task using local records only."""
    db.execute("""CREATE TABLE IF NOT EXISTS correction_reviews (
        fact_id INTEGER PRIMARY KEY, evidence TEXT NOT NULL, updated TEXT NOT NULL)""")
    task=db.execute("""SELECT k.* FROM correction_tasks t
        JOIN knowledge_versions k ON k.id=t.fact_id
        LEFT JOIN correction_reviews r ON r.fact_id=t.fact_id
        WHERE t.status='open' AND k.status='current'
        ORDER BY r.updated IS NOT NULL,r.updated,t.fact_id LIMIT 1""").fetchone()
    if task is None:
        return None
    rows=db.execute("""SELECT id,value,source,status FROM knowledge_versions
        WHERE subject=? AND predicate=? AND id!=? AND status IN ('pending','current')
        ORDER BY id DESC LIMIT 100""",(task["subject"],task["predicate"],task["id"])).fetchall()
    evidence={"support_ids":[],"counterclaim_ids":[],"same_source_ids":[]}
    for row in rows:
        key="same_source_ids" if row["source"]==task["source"] else "support_ids" if row["value"]==task["value"] else "counterclaim_ids"
        evidence[key].append(row["id"])
    evidence["alternatives"]=alternatives(task,rows)
    evidence["status"]="awaiting_verification"
    evidence["limitation"]="Different source labels do not establish independence; pending claims are not verified evidence."
    db.execute("""INSERT INTO correction_reviews VALUES (?,?,?)
        ON CONFLICT(fact_id) DO UPDATE SET evidence=excluded.evidence,updated=excluded.updated""",
        (task["id"],json.dumps(evidence),now()))
    return {"fact_id":task["id"],**evidence}

def alternatives(task,rows):
    """Competing recorded values, not invented causal explanations."""
    groups={}
    for row in [task,*rows]:
        groups.setdefault(row["value"],[]).append(row["id"])
    return {"candidates":[{"value":value,"record_ids":ids,
                "status":"unverified_candidate",
                "test":"Obtain a dated independent observation of this subject and predicate; compare the recorded value."}
                for value,ids in sorted(groups.items())],
            "unknown_possible":True,
            "evidence_sufficient":False,
            "reason":"Local claims alone do not establish independent verification."}
