"""Read-only hypothetical scenarios and recorded knowledge chronology."""
import json
from .database import DB_PATH, connect
from .inference import setup, triple

def simulate(overrides,path=DB_PATH):
    changes=[triple(x) for x in overrides]
    if len(changes)>20 or len({x[:2] for x in changes})!=len(changes):
        raise ValueError("Invalid scenario")
    setup(path)
    with connect(path) as db:
        facts={triple((r["subject"],r["predicate"],r["value"])) for r in db.execute("SELECT * FROM knowledge_versions WHERE status='current'")}
        rules=[(r["id"],[tuple(p) for p in json.loads(r["premises"])],tuple(json.loads(r["conclusion"]))) for r in db.execute("SELECT * FROM inference_rules WHERE kind='causal' ORDER BY id LIMIT 500")]
    def closure(seed,locked):
        known=set(seed)
        for _ in range(10):
            new={c for _,p,c in rules if c[:2] not in locked and all(x in known for x in p)}
            if new<=known:
                break
            known.update(new)
        return known
    keys={x[:2] for x in changes}
    baseline=closure(facts,set())
    alternative=closure({x for x in facts if x[:2] not in keys}|set(changes),keys)
    return {"assumptions":changes,"added":sorted(alternative-baseline),
            "removed":sorted(baseline-alternative),"status":"hypothetical",
            "limitation":"Explicit causal rules only; not a validated causal model."}

def chronology(query,path=DB_PATH):
    from .reasoning import tokens
    setup(path)
    terms=tokens(query)
    with connect(path) as db:
        rows=[dict(r) for r in db.execute("""SELECT id,subject,predicate,value,status,created,ended
            FROM knowledge_versions WHERE status IN ('current','superseded')
            ORDER BY created DESC,id DESC LIMIT 500""")]
    return [r for r in rows if terms & tokens(r["subject"]+" "+r["predicate"])][:10]
