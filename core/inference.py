"""Explicit rule-based deductions; causal claims require explicit causal rules."""
import json
from .database import DB_PATH, connect
from .knowledge import setup as init

def setup(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS inference_rules (
            id INTEGER PRIMARY KEY, premises TEXT NOT NULL, conclusion TEXT NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('deductive','causal')))""")

def triple(value):
    if not isinstance(value,(list,tuple)) or len(value)!=3 or any(not isinstance(x,str) or not x.strip() for x in value):
        raise ValueError("Expected subject, predicate, value")
    return (value[0].strip().casefold(),value[1].strip().casefold(),value[2].strip())

def add_rule(premises,conclusion,kind="deductive",path=DB_PATH):
    if kind not in ("deductive","causal") or not 1<=len(premises)<=10:
        raise ValueError("Invalid rule")
    premises=[triple(p) for p in premises]
    conclusion=triple(conclusion)
    setup(path)
    with connect(path) as db:
        return db.execute("INSERT INTO inference_rules(premises,conclusion,kind) VALUES (?,?,?)",
            (json.dumps(premises),json.dumps(conclusion),kind)).lastrowid

def derive(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        facts={triple((r["subject"],r["predicate"],r["value"])):{"sources":[r["id"]],"rules":[],"confidence":r["confidence"]} for r in db.execute("SELECT * FROM knowledge_versions WHERE status='current'")}
        rules=[(r["id"],r["kind"],[tuple(p) for p in json.loads(r["premises"])],tuple(json.loads(r["conclusion"]))) for r in db.execute("SELECT * FROM inference_rules ORDER BY id LIMIT 500")]
    def closure(blocked):
        known=dict(facts)
        for _ in range(10):
            changed=False
            for rid,kind,premises,c in rules:
                if c in known or c in blocked or any(f[:2]==c[:2] and f!=c for f in facts):
                    continue
                if not all(p in known for p in premises):
                    continue
                evidence=[known[p] for p in premises]
                known[c]={"sources":sorted({s for e in evidence for s in e["sources"]}),
                    "rules":sorted({rid}|{s for e in evidence for s in e["rules"]}),
                    "confidence":min(e["confidence"] for e in evidence),"kind":kind}
                changed=True
            if not changed:
                break
        return known
    initial=closure(set())
    values={}
    for c in initial:
        values.setdefault(c[:2],set()).add(c[2])
    blocked={c for c in initial if c not in facts and len(values[c[:2]])>1}
    clean=closure(blocked)
    results=[]
    for c,e in initial.items():
        if c in facts:
            continue
        proof=clean.get(c,e)
        alternatives=[]
        if c in clean:
            # Recompute with each rule in the selected proof disabled.
            for excluded in proof["rules"][:10]:
                subset=[r for r in rules if r[0]!=excluded]
                original=rules[:]
                rules[:]=subset
                try:
                    alternate=closure(blocked).get(c)
                finally:
                    rules[:]=original
                if alternate and alternate!=proof and alternate not in alternatives:
                    alternatives.append(alternate)
        results.append({"conclusion":c,**proof,"alternative_proofs":alternatives,
            "conflicts_with_confirmed":c not in clean,
            **({"conflict_reason":"inconsistent_derived_proof"} if c not in clean else {})})
    for rid,kind,premises,c in rules:
        if any(f[:2]==c[:2] and f!=c for f in facts) and all(p in clean for p in premises):
            evidence=[clean[p] for p in premises]
            results.append({"conclusion":c,"kind":kind,"sources":sorted({s for e in evidence for s in e["sources"]}),
                "rules":sorted({rid}|{s for e in evidence for s in e["rules"]}),
                "confidence":min(e["confidence"] for e in evidence),"conflicts_with_confirmed":True})
    return results
