"""Finite scenario semantics and four-valued evidence; no unrestricted inference."""
from .inference import triple, setup
from .database import DB_PATH, connect

def modal(proposition, worlds):
    p=triple(proposition)
    worlds=[{triple(f) for f in w} for w in worlds]
    if not worlds:
        raise ValueError("At least one scenario required")
    present=[p in w for w in worlds]
    return {"possible":any(present),"necessary":all(present),
            "absent_in_all":not any(present),"world_count":len(worlds),
            "scope":"supplied scenarios only; absence is not proof of impossibility"}

def evidence(positive,negative):
    return {(True,False):"supported",(False,True):"opposed",
            (True,True):"conflicting",(False,False):"unknown"}[(bool(positive),bool(negative))]

def negate(pair):
    return pair[1],pair[0]

def conjunction(a,b):
    return a[0] and b[0],a[1] or b[1]

def disjunction(a,b):
    return a[0] or b[0],a[1] and b[1]

def assess(query,path=DB_PATH):
    from .reasoning import tokens
    setup(path)
    terms=tokens(query)
    with connect(path) as db:
        rows=[dict(r) for r in db.execute("SELECT * FROM knowledge_versions WHERE status IN ('current','pending') ORDER BY id DESC LIMIT 500")]
    result=[]
    for r in rows:
        if r["status"]!="current" or not terms & tokens(r["subject"]+" "+r["predicate"]):
            continue
        rivals=[p["id"] for p in rows if p["status"]=="pending" and p["subject"]==r["subject"] and p["predicate"]==r["predicate"] and p["value"]!=r["value"]]
        result.append({"proposition":[r["subject"],r["predicate"],r["value"]],
            "state":evidence(True,rivals),"confirmed_source":r["id"],
            "unconfirmed_opposition":rivals,"guidance":"Pending alternatives are not established negations."})
    return result[:10]
