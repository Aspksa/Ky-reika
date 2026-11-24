"""Inspect character evolution without applying changes automatically."""
import json
from .database import DB_PATH, connect, TRAITS
from . import cognition

def report(path=DB_PATH):
    cognition.setup(path)
    with connect(path) as db:
        scores=dict(db.execute("SELECT trait,score FROM personality"))
        proposals=[dict(r) for r in db.execute("SELECT * FROM cognition_proposal ORDER BY id DESC LIMIT 50")]
        for p in proposals:
            p["evidence"]=json.loads(p["evidence"])
        observations=[dict(r) for r in db.execute("SELECT trait,count(*) AS samples FROM cognition_observation WHERE confidence>=.8 GROUP BY trait")]
    return {"traits":[{"trait":trait,"baseline":baseline,"current":scores[trait],
                       "change":scores[trait]-baseline} for trait,baseline in TRAITS.items()],
            "observations":observations,"proposals":proposals,
            "approval_required":True,"automatic_application":False}

def propose(path=DB_PATH):
    return cognition.reflect(path)
