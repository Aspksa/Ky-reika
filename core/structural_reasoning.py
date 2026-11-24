"""Finite monotone rule closure; no causal or universal factual authority."""
from collections import defaultdict, deque
import random

def closure(facts,rules):
    known=set(facts)
    pending=deque(known)
    waiting=defaultdict(list)
    missing=[]
    for i,(premises,target) in enumerate(rules):
        required=set(premises)
        missing.append(len(required))
        for p in required:
            waiting[p].append(i)
        if not required and target not in known:
            known.add(target)
            pending.append(target)
    while pending:
        fact=pending.popleft()
        for i in waiting[fact]:
            missing[i]-=1
            if missing[i]==0:
                target=rules[i][1]
                if target not in known:
                    known.add(target)
                    pending.append(target)
    return known

def reference(facts,rules):
    known=set(facts)
    while True:
        expanded=known|{target for premises,target in rules if set(premises)<=known}
        if expanded==known:
            return known
        known=expanded

def evaluate(seed,count=40):
    rng=random.Random(seed)
    passed=0
    failures=[]
    for i in range(count):
        n=rng.randint(5,25)
        facts=set(rng.sample(range(n),rng.randrange(n+1)))
        rules=[(tuple(rng.sample(range(n),rng.randrange(4))),rng.randrange(n)) for _ in range(n*2)]
        expected=reference(facts,rules)
        actual=closure(facts,rules)
        if actual==expected:
            passed+=1
        else:
            failures.append({"case":i,"missing":sorted(expected-actual),"unexpected":sorted(actual-expected)})
    return {"passed":passed,"cases":count,"failures":failures,"status":"validated_on_sample" if passed==count else "review_required",
            "scope":"finite monotone conjunctive rules; no negation or conflict resolution"}
