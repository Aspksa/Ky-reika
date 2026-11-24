"""Competing predictive models, not established explanatory laws."""
import json
from .database import DB_PATH,connect,now
from .discovery_lab import recent

def compare(predictions):
    groups={}
    for p in predictions:
        if p["status"] not in ("observed_match","observed_counterexample","awaiting_evidence"):
            continue
        subject,predicate,value=p["candidate"]
        group=groups.setdefault((predicate,value),{})
        group[subject]=p
    result=[]
    for (predicate,value),items in sorted(groups.items()):
        matches=sum(p["status"]=="observed_match" for p in items.values())
        misses=sum(p["status"]=="observed_counterexample" for p in items.values())
        evaluated=matches+misses
        result.append({"property":[predicate,value],"models":[
            {"name":"property_transfer","correct":matches},
            {"name":"nontransfer","correct":misses}],
            "evaluated":evaluated,"pending":len(items)-evaluated,
            "preferred":("property_transfer" if matches>misses else "nontransfer") if evaluated>=5 and abs(matches-misses)>=3 else None,
            "observation_ids":sorted({p["observation_id"] for p in items.values() if p["status"] in ("observed_match","observed_counterexample") and p["observation_id"] is not None}),
            "status":"provisional_comparison","limitation":"Selected observations only; no causal identification or independent validation."})
    return result

def refresh(path=DB_PATH):
    report=compare(recent(path))
    with connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS theoretical_comparisons (id INTEGER PRIMARY KEY, content TEXT NOT NULL, created TEXT NOT NULL)")
        content=json.dumps(report,ensure_ascii=False,sort_keys=True)
        old=db.execute("SELECT content FROM theoretical_comparisons ORDER BY id DESC LIMIT 1").fetchone()
        if not old or old["content"]!=content:
            db.execute("INSERT INTO theoretical_comparisons(content,created) VALUES (?,?)",(content,now()))
    return report

def current(path=DB_PATH):
    return compare(recent(path))
