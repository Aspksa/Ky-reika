"""Track observed prediction errors without claiming calibrated intelligence."""
import json
from .database import DB_PATH, connect, now
from .prediction_checks import recent as checks

def refresh(path=DB_PATH):
    observations=checks(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS prediction_lessons (
            id TEXT NOT NULL, revision INTEGER NOT NULL, sequence INTEGER NOT NULL,
            content TEXT NOT NULL, created TEXT NOT NULL, PRIMARY KEY(id,revision,sequence))""")
        db.execute("BEGIN IMMEDIATE")
        for item in observations:
            status=item["status"]
            guidance={
                "contradicting_observation":"Reconsider premises, scope and competing explanations; do not reuse this prediction as established knowledge.",
                "supported_observation":"Retain as limited observational support; seek independent replication.",
                "awaiting_observation":"Do not infer success or failure without observations."
            }[status]
            content=json.dumps({**item,"guidance":guidance},sort_keys=True,ensure_ascii=False)
            key=(item["id"],item["revision"])
            old=db.execute("SELECT sequence,content FROM prediction_lessons WHERE id=? AND revision=? ORDER BY sequence DESC LIMIT 1",key).fetchone()
            if not old or old["content"]!=content:
                db.execute("INSERT INTO prediction_lessons VALUES (?,?,?,?,?)",
                    (*key,old["sequence"]+1 if old else 1,content,now()))

def profile(path=DB_PATH):
    active={(r["id"],r["revision"]):r for r in checks(path)}
    with connect(path) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='prediction_lessons'").fetchone():
            return {"lessons":[],"evaluated":0,"observed_match_rate":None}
        lessons=[]
        for row in db.execute("""SELECT p.* FROM prediction_lessons p JOIN
            (SELECT id,revision,max(sequence) sequence FROM prediction_lessons GROUP BY id,revision) v
            ON p.id=v.id AND p.revision=v.revision AND p.sequence=v.sequence ORDER BY p.created DESC"""):
            item=json.loads(row["content"])
            current=active.get((row["id"],row["revision"]))
            if current and all(item[k]==current[k] for k in ("status","sources","observable")):
                lessons.append(item)
    evaluated=[r for r in lessons if r["status"]!="awaiting_observation"]
    return {"lessons":lessons,"evaluated":len(evaluated),
        "observed_match_rate":sum(r["status"]=="supported_observation" for r in evaluated)/len(evaluated) if evaluated else None,
        "limitation":"Current selected predictions only; not calibrated accuracy or independent causal validation."}
