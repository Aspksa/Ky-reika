"""Live database counts, not inferred intelligence scores."""
from .database import connect, DB_PATH, now
from .dispatcher import STAGES

METRICS={"words":("language_exposure","count(*)"),"definitions":("semantic_definitions","count(DISTINCT term)"),"memories":("memories","count(*)"),"facts":("knowledge_versions","count(*) WHERE status='current'"),"messages":("messages","count(*)"),"research":("research_goals","count(*)")}

def report(path=DB_PATH):
    with connect(path) as db:
        db.execute("BEGIN")
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        metrics={}
        for key,(table,expression) in METRICS.items():
            aggregate,_,where=expression.partition(" WHERE ")
            metrics[key]=db.execute("SELECT "+aggregate+" FROM "+table+(" WHERE "+where if where else "")).fetchone()[0] if table in tables else None
        stages={r["stage"]:dict(r) for r in db.execute("SELECT * FROM maintenance_status")} if "maintenance_status" in tables else {}
        return {"time":now(),"metrics":metrics,"stages":[{"stage":name,"module":module,**stages.get(name,{"status":"unobserved"})} for name,module,_,_ in STAGES]}
