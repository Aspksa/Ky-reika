"""Explicit rule-based deductions; causal claims require explicit causal rules."""
import json
import logging
from functools import lru_cache
from copy import deepcopy
from time import perf_counter_ns
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
        db.execute("BEGIN")
        facts={triple((r["subject"],r["predicate"],r["value"])):{"sources":[r["id"]],"rules":[],"confidence":r["confidence"]} for r in db.execute("SELECT * FROM knowledge_versions WHERE status='current' ORDER BY id")}
        rules=[(r["id"],r["kind"],[tuple(p) for p in json.loads(r["premises"])],tuple(json.loads(r["conclusion"]))) for r in db.execute("SELECT * FROM inference_rules ORDER BY id LIMIT 500")]
    snapshot=json.dumps([list(facts.items()),rules],ensure_ascii=False,separators=(",",":"))
    return deepcopy(_derive_snapshot(str(path),snapshot))

@lru_cache(maxsize=8)
def _derive_snapshot(path,snapshot):
    raw_facts,raw_rules=json.loads(snapshot)
    facts={tuple(f):e for f,e in raw_facts}
    rules=[(rid,kind,[tuple(p) for p in premises],tuple(c)) for rid,kind,premises,c in raw_rules]
    fact_values={f[:2]:f[2] for f in facts}
    def contradicts(c):
        return c[:2] in fact_values and fact_values[c[:2]]!=c[2]
    def reference_closure(blocked,excluded=None):
        known=dict(facts)
        for _ in range(len(rules)+1):
            changed=False
            for rid,kind,premises,c in rules:
                if rid==excluded or c in known or c in blocked or contradicts(c):
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
    def indexed_proofs(blocked,excluded=None):
        import heapq
        known=dict(facts)
        eligible=[(rid,kind,premises,c) for rid,kind,premises,c in rules
                  if rid!=excluded and c not in blocked and not contradicts(c)]
        waiting={}
        missing=[]
        queue=[]
        for i,(_,_,premises,c) in enumerate(eligible):
            absent=set(premises)-known.keys()
            missing.append(len(absent))
            for p in absent:
                waiting.setdefault(p,[]).append(i)
            if not absent:
                heapq.heappush(queue,(0,i))
        while queue:
            turn,i=heapq.heappop(queue)
            rid,kind,premises,c=eligible[i]
            if c in known:
                continue
            evidence=[known[p] for p in premises]
            known[c]={"sources":sorted({s for e in evidence for s in e["sources"]}),
                "rules":sorted({rid}|{s for e in evidence for s in e["rules"]}),
                "confidence":min(e["confidence"] for e in evidence),"kind":kind}
            for j in waiting.get(c,[]):
                missing[j]-=1
                if missing[j]==0:
                    heapq.heappush(queue,(turn+int(j<=i),j))
        return known
    trials=[]
    def closure(blocked,excluded=None):
        # Keep proof construction authoritative; compare the indexed reachability
        # algorithm on the exact same filtered rules before trusting its output.
        eligible=[(premises,c) for rid,kind,premises,c in rules
                  if rid!=excluded and c not in blocked and not contradicts(c)]
        start=perf_counter_ns()
        known=reference_closure(blocked,excluded)
        reference_ns=perf_counter_ns()-start
        start=perf_counter_ns()
        status="error"
        try:
            predicted=indexed_proofs(blocked,excluded)
            status="match" if predicted==known else "mismatch"
            if predicted!=known:
                logging.getLogger(__name__).warning("Indexed closure mismatch; retaining reference proofs")
        except Exception:
            logging.getLogger(__name__).exception("Indexed closure failed; retaining reference proofs")
        trials.append((status,reference_ns,perf_counter_ns()-start,len(eligible)))
        return predicted if status=="match" and trials[-1][2]<reference_ns else known
    initial=closure(set())
    values={}
    for c in initial:
        values.setdefault(c[:2],set()).add(c[2])
    blocked={c for c in initial if c not in facts and len(values[c[:2]])>1}
    clean=closure(blocked)
    results=[]
    alternate_cache={}
    # Bound retained closures to avoid unbounded memory growth.
    for c,e in initial.items():
        if c in facts:
            continue
        proof=clean.get(c,e)
        alternatives=[]
        if c in clean:
            # Recompute with each rule in the selected proof disabled.
            for excluded in proof["rules"][:10]:
                if excluded not in alternate_cache:
                    if len(alternate_cache)>=16:
                        alternate_cache.pop(next(iter(alternate_cache)))
                    alternate_cache[excluded]=closure(blocked,excluded)
                alternate=alternate_cache[excluded].get(c)
                if alternate and alternate!=proof and alternate not in alternatives:
                    alternatives.append(alternate)
        results.append({"conclusion":c,**proof,"alternative_proofs":alternatives,
            "conflicts_with_confirmed":c not in clean,
            **({"conflict_reason":"inconsistent_derived_proof"} if c not in clean else {})})
    for rid,kind,premises,c in rules:
        if contradicts(c) and all(p in clean for p in premises):
            evidence=[clean[p] for p in premises]
            results.append({"conclusion":c,"kind":kind,"sources":sorted({s for e in evidence for s in e["sources"]}),
                "rules":sorted({rid}|{s for e in evidence for s in e["rules"]}),
                "confidence":min(e["confidence"] for e in evidence),"conflicts_with_confirmed":True})
    try:
        from .inference_metrics import record
        record(path,trials)
    except Exception:
        logging.getLogger(__name__).exception("Inference metrics unavailable")
    return results
