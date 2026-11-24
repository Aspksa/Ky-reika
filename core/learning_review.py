"""Conservative strategy evaluation on separate chronological feedback samples."""
import json
from .database import DB_PATH, connect, now
from .adaptation import setup as init

def evaluate(rows):
    modes={}
    for row in rows:
        modes.setdefault(row["mode"],[]).append(row["rating"])
    if any(len(modes.get(m,[]))<10 for m in ("direct","structured")):
        return {"preferred":None,"status":"insufficient_feedback"}
    stats={}
    for m in ("direct","structured"):
        values=modes[m]
        split=len(values)//2
        stats[m]={"samples":len(values),"training":sum(values[:split])/split,
                  "validation":sum(values[split:])/len(values[split:])}
    a,b=stats["structured"],stats["direct"]
    preferred="structured" if a["training"]-b["training"]>=.3 and a["validation"]-b["validation"]>=.3 else None
    recent={m:modes[m][-10:] for m in ("direct","structured")}
    recent_gap=sum(recent["structured"])/10-sum(recent["direct"])/10
    if preferred and recent_gap<.3:
        preferred=None
    return {"preferred":preferred,"status":"observational","scores":stats,
            "recent_gap":recent_gap,"drift_warning":recent_gap<0 and a["training"]-b["training"]>=.3}

def refresh(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS learning_reviews (
            task TEXT PRIMARY KEY, report TEXT NOT NULL, updated TEXT NOT NULL)""")
        rows=[dict(r) for r in db.execute("""SELECT u.task,u.mode,f.rating FROM strategy_usage u
            JOIN response_feedback f ON f.message_id=u.message_id ORDER BY f.created,u.message_id""")]
        groups={}
        for r in rows:
            groups.setdefault(r["task"],[]).append(r)
        db.execute("DELETE FROM learning_reviews")
        db.executemany("INSERT INTO learning_reviews VALUES (?,?,?)",
            [(task,json.dumps(evaluate(group)),now()) for task,group in groups.items()])
    return len(groups)
