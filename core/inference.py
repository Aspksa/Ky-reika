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
        rules=list(db.execute("SELECT * FROM inference_rules ORDER BY id LIMIT 500"))
    known=dict(facts)
    results=[]
    for _ in range(10):
        changed=False
        for rule in rules:
            premises=[tuple(p) for p in json.loads(rule["premises"])]
            conclusion=tuple(json.loads(rule["conclusion"]))
            if conclusion in known or not all(p in known for p in premises):
                continue
            evidence=[known[p] for p in premises]
            item={"sources":sorted({s for e in evidence for s in e["sources"]}),
                  "rules":sorted({rule["id"]}|{s for e in evidence for s in e["rules"]}),
                  "confidence":min(e["confidence"] for e in evidence)}
            conflict=any(f[:2]==conclusion[:2] and f[2]!=conclusion[2] for f in facts)
            if not conflict:
                known[conclusion]=item
            results.append({"conclusion":conclusion,"kind":rule["kind"],**item,
                "conflicts_with_confirmed":conflict})
            changed=changed or not conflict
        if not changed:
            break
    unique={tuple(r["conclusion"]):r for r in results}
    # Quarantine mutually inconsistent derived values and every proof using them.
    values={}
    for conclusion in known:
        values.setdefault(conclusion[:2],set()).add(conclusion[2])
    blocked={c for c in known if c not in facts and len(values[c[:2]])>1}
    rule_map={r["id"]:r for r in rules}
    for item in unique.values():
        dependencies={tuple(p) for rid in item["rules"]
                      for p in json.loads(rule_map[rid]["premises"])}
        if tuple(item["conclusion"]) in blocked or dependencies & blocked:
            item["conflicts_with_confirmed"]=True
            item["conflict_reason"]="inconsistent_derived_proof"
    return list(unique.values())
