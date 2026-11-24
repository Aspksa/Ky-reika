"""Observed concept relations, not universal taxonomy or causal rules."""
from itertools import combinations
from .database import DB_PATH, connect
from .knowledge import setup

def discover(rows):
    groups={}
    for r in rows:
        groups.setdefault((r["predicate"],r["value"]),{})[r["subject"]]=r["id"]
    groups={k:v for k,v in groups.items() if len(v)>=3}
    keys=sorted(groups,key=lambda k:(-len(groups[k]),k))[:100]
    result=[]
    for a,b in combinations(keys,2):
        x,y=groups[a],groups[b]
        shared=set(x)&set(y)
        if len(shared)<3:
            continue
        if set(x)==set(y):
            relation="observed_coextension"
        elif set(x)<set(y):
            relation="observed_subset"
        elif set(y)<set(x):
            a,b=b,a
            x,y=y,x
            relation="observed_subset"
        else:
            relation="observed_overlap"
        result.append({"left":list(a),"right":list(b),"relation":relation,
            "shared_subjects":sorted(shared)[:10],"shared_count":len(shared),
            "source_ids":sorted({x[s] for s in shared}|{y[s] for s in shared}),
            "left_only_ids":sorted(x[s] for s in set(x)-shared),
            "right_only_ids":sorted(y[s] for s in set(y)-shared),
            "status":"candidate_relation","deductive_authority":False})
    return sorted(result,key=lambda r:(-r["shared_count"],r["left"],r["right"]))[:100]

def relevant(message,path=DB_PATH):
    from .reasoning import tokens
    setup(path)
    with connect(path) as db:
        rows=[dict(r) for r in db.execute("SELECT id,subject,predicate,value FROM knowledge_versions WHERE status='current' ORDER BY id DESC LIMIT 2000")]
    terms=tokens(message)
    return [r for r in discover(rows) if terms & tokens(" ".join(r["left"]+r["right"]+r["shared_subjects"]))][:5]
