"""Operational novelty statistics, not evidence of reasoning correctness."""
import json
from .database import DB_PATH, connect

def summarize(rows):
    groups={}
    for row in rows:
        mode=row.get("mode")
        if mode not in ("audit","alternative","synthesis","decompose") or not isinstance(row.get("repetition_detected"),bool):
            continue
        group=groups.setdefault(mode,{"samples":0,"repeated":0})
        group["samples"]+=1
        group["repeated"]+=int(row["repetition_detected"])
    for group in groups.values():
        group["novelty_rate"]=1-group["repeated"]/group["samples"]
    return groups

def prefer(default,stats):
    if default not in ("audit","alternative","synthesis"):
        return default
    base=stats.get(default,{})
    if base.get("samples",0)<10:
        return default
    eligible=[m for m in ("audit","alternative","synthesis") if
        stats.get(m,{}).get("samples",0)>=10 and
        stats[m]["novelty_rate"]>=base["novelty_rate"]+.2]
    return max(eligible,key=lambda m:stats[m]["novelty_rate"]) if eligible else default

def profile(path=DB_PATH,exclude_root=None):
    with connect(path) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='deep_inquiry'").fetchone():
            return {}
        rows=db.execute("""SELECT content FROM deep_inquiry WHERE status IN ('unverified','awaiting_evidence')
            AND content IS NOT NULL AND (? IS NULL OR root<>?) ORDER BY created DESC LIMIT 300""",(exclude_root,exclude_root))
        return summarize(json.loads(r["content"]) for r in rows)
