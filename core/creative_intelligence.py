"""Combinatorial creativity grounded in observed properties; candidates are not facts."""
from .database import DB_PATH, connect
from .knowledge import setup
from .concept_relations import discover

def generate(rows):
    ideas=[]
    for relation in discover(rows):
        if relation["relation"]!="observed_overlap":
            continue
        for side,other in (("left","right"),("right","left")):
            predicate,value=relation[other]
            for sid in relation[side+"_only_ids"]:
                source=next(r for r in rows if r["id"]==sid)
                subject=source["subject"]
                existing=[r for r in rows if r["subject"]==subject and r["predicate"]==predicate]
                if existing:
                    continue
                ideas.append({"candidate":[subject,predicate,value],
                    "source_ids":sorted(set(relation["source_ids"]+[sid])),
                    "method":"property_combination","status":"unverified_hypothesis",
                    "novelty":"not_observed_in_sample",
                    "next_test":"Obtain independent evidence for the missing property and check counterexamples.",
                    "limitation":"Overlap does not imply transfer; novelty is relative to the sampled records."})
    unique={tuple(i["candidate"]):i for i in ideas}
    return list(unique.values())[:50]

def relevant(message,path=DB_PATH):
    from .reasoning import tokens
    setup(path)
    with connect(path) as db:
        rows=[dict(r) for r in db.execute("SELECT id,subject,predicate,value FROM knowledge_versions WHERE status='current' ORDER BY id DESC LIMIT 2000")]
    terms=tokens(message)
    return [i for i in generate(rows) if terms & tokens(" ".join(i["candidate"]))][:5]
