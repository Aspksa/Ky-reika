"""Transfer experiments for graph reachability, not arbitrary causal inference."""
import random
from .generative_methods import solve

def evaluate(selection,seed):
    method=selection.get("method")
    if selection.get("status")!="validated" or method is None:
        return {"status":"not_eligible","cases":0}
    rng=random.Random(seed)
    results={}
    for family in ("branching","disconnected","cyclic"):
        passed=0
        for _ in range(20):
            n=rng.randint(5,25)
            if family=="branching":
                edges=[(rng.randrange(i),i) for i in range(1,n)]
                expected=set(range(n))
            elif family=="disconnected":
                split=rng.randint(2,n-2)
                edges=[(i,i+1) for i in range(n-1) if i!=split-1]
                expected=set(range(split))
            else:
                edges=[(i,(i+1)%n) for i in range(n)]
                expected=set(range(n))
            # Relabel nodes to test structural rather than lexical similarity.
            labels=rng.sample(range(100,10000),n)
            actual,_=solve([(labels[a],labels[b]) for a,b in edges],labels[0],method)
            passed+=int(actual=={labels[i] for i in expected})
        results[family]=passed
    return {"status":"transfer_validated" if all(v==20 for v in results.values()) else "transfer_failed",
            "cases":60,"passed":results,"method":method,
            "scope":"synthetic single-premise graph reachability",
            "limitation":"Does not establish transfer to conjunctive rules or general reasoning."}
