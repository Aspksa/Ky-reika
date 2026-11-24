"""Bounded local scheduling based on backlog, not claimed intelligence."""
from .database import DB_PATH, connect

def choose(backlog, changes):
    budget=5 if backlog<=5 else 10 if backlog<=20 else 20
    if backlog and changes.get("thought_steps")==0:
        budget=min(30,budget+5)
    return {"backlog":backlog,"thought_budget":budget,
            "interval":900 if backlog>20 else 1800 if backlog else 3600}

def policy(path=DB_PATH):
    from .thought_tree import setup
    from .growth_metrics import latest
    setup(path)
    with connect(path) as db:
        backlog=db.execute("""SELECT count(*) FROM development_thoughts d
            WHERE status='candidate' AND NOT EXISTS (
            SELECT 1 FROM thought_nodes n WHERE n.root=d.fingerprint
            AND n.revision=d.observations AND n.stage=2)""").fetchone()[0]
    return choose(backlog,latest(path).get("changes",{}))
