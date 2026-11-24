"""Generate safe strategy combinations without executing generated source code."""
from itertools import product
import random

def solve(edges,start,method):
    pending=[start]
    seen={start}
    work=0
    index={}
    if method["indexed"]:
        for a,b in edges:
            index.setdefault(a,[]).append(b)
            work+=1
    while pending:
        a=pending.pop(0 if method["fifo"] else -1)
        neighbors=index.get(a,[]) if method["indexed"] else [y for x,y in edges if x==a]
        work+=len(neighbors) if method["indexed"] else len(edges)
        for b in neighbors:
            if b not in seen:
                seen.add(b)
                pending.append(b)
    return seen,work

def cases(seed):
    rng=random.Random(seed)
    for _ in range(24):
        n=rng.randint(4,30)
        edges=[(a,b) for a in range(n) for b in range(n) if rng.random()<.12]
        start=rng.randrange(n)
        # Independent reference: bounded synchronous closure.
        expected={start}
        for _ in range(n):
            expected |= {b for a,b in edges if a in expected}
        yield edges,start,expected

def assess(method,examples):
    passed=work=0
    for edges,start,expected in examples:
        actual,cost=solve(edges,start,method)
        passed+=int(actual==expected)
        work+=cost
    return {"passed":passed,"work":work}

def experiment(seed):
    training=list(cases(seed))
    validation=list(cases(seed+2000003))
    baseline={"indexed":False,"fifo":False}
    candidates=[{"indexed":a,"fifo":b} for a,b in product((False,True),repeat=2)]
    results=[{"method":m,"training":assess(m,training),"validation":assess(m,validation)} for m in candidates]
    base=results[0]
    eligible=[r for r in results if all(r[k]["passed"]==24 and r[k]["work"]<base[k]["work"] for k in ("training","validation"))]
    best=min(eligible,key=lambda r:r["training"]["work"]) if eligible else None
    return {"candidates":results,"preferred":best["method"] if best else baseline,
            "status":"validated_candidate" if best else "baseline_retained",
            "limitation":"Synthetic graph tasks and operation counts only; no production code replacement."}
