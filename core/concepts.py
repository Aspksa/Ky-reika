"""Inductive concept candidates, never automatic factual generalizations."""
from collections import defaultdict
from .database import DB_PATH, connect
from .knowledge import setup
from functools import lru_cache
from copy import deepcopy

def discover(rows):
    groups=defaultdict(lambda:defaultdict(list))
    for r in rows:
        groups[r["predicate"]][r["value"]].append(r)
    concepts=[]
    for predicate,values in groups.items():
        total=sum(len(items) for items in values.values())
        for value,items in values.items():
            if len({r["subject"] for r in items})<3:
                continue
            exceptions=[r for other,records in values.items() if other!=value for r in records]
            concepts.append({"property":[predicate,value],"examples":[r["subject"] for r in items[:10]],
                "source_ids":[r["id"] for r in items],"counterexample_ids":[r["id"] for r in exceptions],
                "observed_fraction":len(items)/total,"status":"candidate_abstraction",
                "limitation":"Shared observed property, not a universal rule or causal explanation."})
    return sorted(concepts,key=lambda c:(-len(c["source_ids"]),c["property"]))[:30]

@lru_cache(maxsize=4)
def _cached(snapshot):
    return discover([dict(zip(("id","subject","predicate","value"),row)) for row in snapshot])

def relevant(message,path=DB_PATH):
    from .reasoning import tokens
    setup(path)
    with connect(path) as db:
        snapshot=tuple(tuple(r) for r in db.execute("SELECT id,subject,predicate,value FROM knowledge_versions WHERE status='current' ORDER BY id DESC LIMIT 2000"))
    terms=tokens(message)
    return [c for c in deepcopy(_cached(snapshot)) if terms & tokens(" ".join(c["property"]+c["examples"]))][:5]
