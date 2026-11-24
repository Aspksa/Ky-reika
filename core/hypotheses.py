"""Bounded induction and abduction; neither establishes truth."""
import json
from collections import defaultdict, Counter
from .database import DB_PATH, connect
from .inference import setup, triple

def analyze(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        facts={triple((r["subject"],r["predicate"],r["value"])):r["id"] for r in db.execute("SELECT * FROM knowledge_versions WHERE status='current'")}
        rules=list(db.execute("SELECT * FROM inference_rules ORDER BY id LIMIT 500"))
    groups=defaultdict(list)
    for (subject,predicate,value),source in facts.items():
        groups[predicate].append((value,source))
    patterns=[]
    for predicate,observations in groups.items():
        if len(observations)<3:
            continue
        counts=Counter(v for v,_ in observations)
        for value,count in counts.items():
            if count>=3 and count/len(observations)>=.75:
                patterns.append({"predicate":predicate,"value":value,"support":count,
                    "sample_size":len(observations),"observed_frequency":count/len(observations),
                    "sources":[s for v,s in observations if v==value],"status":"hypothesis"})
    explanations=[]
    for rule in rules:
        conclusion=tuple(json.loads(rule["conclusion"]))
        if conclusion not in facts:
            continue
        premises=[tuple(p) for p in json.loads(rule["premises"])]
        missing=[p for p in premises if p not in facts]
        if not missing or any(f[:2]==p[:2] and f[2]!=p[2] for p in missing for f in facts):
            continue
        explanations.append({"observation":conclusion,"possible_conditions":missing,
            "rule":rule["id"],"observation_source":facts[conclusion],
            "matched_sources":[facts[p] for p in premises if p in facts],
            "status":"unverified_explanation"})
    return {"patterns":sorted(patterns,key=lambda p:p["support"],reverse=True)[:50],
            "explanations":sorted(explanations,key=lambda e:len(e["possible_conditions"]))[:50]}
