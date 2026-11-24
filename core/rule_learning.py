"""Empirical rule proposals; associations are not causal or deductive laws."""
from collections import defaultdict, Counter
from .database import DB_PATH, connect
from .knowledge import setup

def discover(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        rows=list(db.execute("SELECT id,subject,predicate,value FROM knowledge_versions WHERE status='current' ORDER BY id DESC LIMIT 2000"))
    subjects=defaultdict(dict)
    for r in rows:
        subjects[r["subject"]][r["predicate"]]=(r["value"],r["id"])
    train=Counter()
    pairs=Counter()
    validation=[]
    for index,(subject,fields) in enumerate(sorted(subjects.items())):
        items=sorted((p,v[0]) for p,v in fields.items())[:20]
        if index%3==0:
            validation.append((subject,fields))
            continue
        for a in items:
            train[a]+=1
            for b in items:
                if a[0]!=b[0]:
                    pairs[a,b]+=1
    proposals=[]
    for (a,b),count in pairs.most_common(500):
        if count<3 or count/train[a]<.8:
            continue
        supporting=[]
        opposing=[]
        for subject,fields in validation:
            if a[0] not in fields or fields[a[0]][0]!=a[1] or b[0] not in fields:
                continue
            target=supporting if fields[b[0]][0]==b[1] else opposing
            target.append({"subject":subject,"sources":[fields[a[0]][1],fields[b[0]][1]]})
        n=len(supporting)+len(opposing)
        proposals.append({"premise":a,"conclusion":b,"training_support":count,
            "training_frequency":count/train[a],"validation_support":supporting,
            "counterexamples":opposing,"validation_frequency":len(supporting)/n if n else None,
            "status":"candidate_supported" if n>=3 and len(supporting)/n>=.8 else "needs_evidence",
            "kind":"association_not_causal"})
    return proposals[:50]
