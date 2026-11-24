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
        from .skill_registry import catalog
        return {"time":now(),"metrics":metrics,"skills":catalog(db,tables,stages),"stages":[{"stage":name,"module":module,**stages.get(name,{"status":"unobserved"})} for name,module,_,_ in STAGES]}

def snapshot(path=DB_PATH):
    import json
    import time
    data=report(path)
    with connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS statistics_history (bucket INTEGER PRIMARY KEY, time TEXT NOT NULL, metrics TEXT NOT NULL)")
        bucket=int(time.time())//60
        db.execute("INSERT OR REPLACE INTO statistics_history VALUES (?,?,?)",(bucket,data["time"],json.dumps(data["metrics"])))
        db.execute("DELETE FROM statistics_history WHERE bucket<?",(bucket-525600,))

def history(path=DB_PATH,limit=720):
    import json
    with connect(path) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='statistics_history' AND type='table'").fetchone():
            return []
        rows=db.execute("SELECT time,metrics FROM statistics_history ORDER BY bucket DESC LIMIT ?",(min(10080,max(1,limit)),)).fetchall()
        return [{"time":r["time"],"metrics":json.loads(r["metrics"])} for r in reversed(rows)]
