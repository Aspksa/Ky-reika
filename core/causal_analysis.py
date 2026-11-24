"""Causal rule analysis, conditional on supplied rules rather than empirical validation."""
import json
from .database import DB_PATH, connect
from .inference import setup

def trace(facts,rules):
    known={tuple(f):{"depth":0,"sources":[sid],"rules":[]} for f,sid in facts}
    for _ in range(len(rules)+1):
        additions={}
        for rid,premises,c in rules:
            if c in known or not all(p in known for p in premises):
                continue
            evidence=[known[p] for p in premises]
            additions.setdefault(c,{"depth":1+max((e["depth"] for e in evidence),default=0),
                "sources":sorted({s for e in evidence for s in e["sources"]}),
                "rules":sorted({rid}|{s for e in evidence for s in e["rules"]})})
        if not additions:
            break
        known.update(additions)
    values={}
    for c in known:
        values.setdefault(c[:2],set()).add(c[2])
    conflicts={c for c in known if len(values[c[:2]])>1}
    # Conservatively propagate uncertainty through any affected causal rule.
    for _ in range(len(known)):
        affected={c for _,p,c in rules if c in known and all(x in known for x in p) and any(x in conflicts for x in p)}
        if affected<=conflicts:
            break
        conflicts.update(affected)
    result=[]
    for c,e in known.items():
        if not e["depth"]:
            continue
        alternatives=[{"rule":rid,"conditions":p} for rid,p,target in rules if target==c and all(x in known and x not in conflicts for x in p)]
        result.append({"conclusion":c,**e,"sufficient_conditions":alternatives,
            "status":"disputed" if c in conflicts else "conditional_prediction",
            "limitation":"Explicit causal rules only; no empirical causal identification."})
    return result

def relevant(message,path=DB_PATH):
    from .reasoning import tokens
    setup(path)
    with connect(path) as db:
        facts=[((r["subject"],r["predicate"],r["value"]),r["id"]) for r in db.execute("SELECT * FROM knowledge_versions WHERE status='current'")]
        rules=[(r["id"],[tuple(p) for p in json.loads(r["premises"])],tuple(json.loads(r["conclusion"]))) for r in db.execute("SELECT * FROM inference_rules WHERE kind='causal' ORDER BY id LIMIT 500")]
    terms=tokens(message)
    return [r for r in trace(facts,rules) if terms & tokens(" ".join(r["conclusion"]))][:8]
