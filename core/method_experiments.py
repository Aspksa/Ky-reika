"""Local method experiments; selection is limited to synthetic reachability tasks."""
import random

def scan(edges,seed):
    reached={seed}
    while True:
        expanded=reached|{b for a,b in edges if a in reached}
        if expanded==reached:
            return reached
        reached=expanded

def frontier(edges,seed):
    adjacency={}
    for a,b in edges:
        adjacency.setdefault(a,[]).append(b)
    reached={seed}
    pending=[seed]
    while pending:
        for b in adjacency.get(pending.pop(),[]):
            if b not in reached:
                reached.add(b)
                pending.append(b)
    return reached

def evaluate(seed=42,count=20):
    rng=random.Random(seed)
    scores={"scan":0,"frontier":0}
    for _ in range(count):
        n=rng.randint(3,20)
        edges=[(i,i+1) for i in range(n-1)]
        edges.extend([(n-1,0),(n+1,n+2)])
        rng.shuffle(edges)
        expected=set(range(n))
        for name,method in (("scan",scan),("frontier",frontier)):
            scores[name]+=int(method(edges,0)==expected)
    return scores

def compare(seed):
    training=evaluate(seed)
    validation=evaluate(seed+1000003)
    eligible=[k for k in training if training[k]==20 and validation[k]==20]
    return {"training":training,"validation":validation,"eligible":eligible,
            "preferred":max(eligible,key=lambda k:(validation[k],training[k],k=="scan")) if eligible else None,
            "status":"synthetic_validation","limitation":"Reachability only; ties retain baseline scan. No production method replacement."}
