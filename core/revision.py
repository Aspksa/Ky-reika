"""Recompute conclusions and retain their revision history."""
import json
from .database import DB_PATH, connect, now
from .inference import setup as init, derive

def setup(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS deduction_history (
            id INTEGER PRIMARY KEY, conclusion TEXT NOT NULL, evidence TEXT NOT NULL,
            created TEXT NOT NULL, withdrawn TEXT)""")
        db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS deduction_active
            ON deduction_history(conclusion) WHERE withdrawn IS NULL""")

def revise(path=DB_PATH):
    setup(path)
    candidates=derive(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        sources={r[0] for r in db.execute("SELECT id FROM knowledge_versions WHERE status='current'")}
        rules={r[0] for r in db.execute("SELECT id FROM inference_rules")}
        valid={json.dumps(x["conclusion"],ensure_ascii=False):json.dumps(x,ensure_ascii=False,sort_keys=True)
               for x in candidates if not x["conflicts_with_confirmed"] and set(x["sources"])<=sources and set(x["rules"])<=rules}
        old={r["conclusion"]:r for r in db.execute("SELECT * FROM deduction_history WHERE withdrawn IS NULL")}
        removed=0
        added=0
        restored=0
        revised=0
        historical={r[0] for r in db.execute("SELECT DISTINCT conclusion FROM deduction_history WHERE withdrawn IS NOT NULL")}
        for key,row in old.items():
            if valid.get(key)!=row["evidence"]:
                db.execute("UPDATE deduction_history SET withdrawn=? WHERE id=?",(now(),row["id"]))
                removed+=1
        for key,value in valid.items():
            if key not in old or old[key]["evidence"]!=value:
                db.execute("INSERT INTO deduction_history(conclusion,evidence,created) VALUES (?,?,?)",(key,value,now()))
                added+=1
                if key in old:
                    revised+=1
                elif key in historical:
                    restored+=1
    return {"added":added,"withdrawn":removed,"active":len(valid),"restored":restored,"revised":revised}

def audit(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        sources={r[0] for r in db.execute("SELECT id FROM knowledge_versions WHERE status='current'")}
        rules={r[0] for r in db.execute("SELECT id FROM inference_rules")}
        rows=list(db.execute("SELECT id,evidence FROM deduction_history WHERE withdrawn IS NULL"))
    stale=[]
    for row in rows:
        evidence=json.loads(row["evidence"])
        if not set(evidence["sources"])<=sources or not set(evidence["rules"])<=rules:
            stale.append(row["id"])
    return {"active_records":len(rows),"stale_records":stale,
            "guidance":"Stored deductions are provisional; use current evidence for conclusions."}

def history(conclusion,path=DB_PATH):
    """Return chronological proof versions, including withdrawn ones."""
    from .inference import triple
    setup(path)
    key=json.dumps(triple(conclusion),ensure_ascii=False)
    with connect(path) as db:
        return [{"id":r["id"],"evidence":json.loads(r["evidence"]),
                 "created":r["created"],"withdrawn":r["withdrawn"]}
                for r in db.execute("SELECT * FROM deduction_history WHERE conclusion=? ORDER BY id",(key,))]
