"""Retry failed maintenance on later cycles, without replaying partial writes immediately."""
import logging
from importlib import import_module
from .database import connect, now

def execute(stages,path,record=None):
    outcomes={}
    for name,action,dependencies in stages:
        if any(outcomes.get(dep)!="ok" for dep in dependencies):
            status="skipped_dependency"
        else:
            try:
                action()
                status="ok"
            except Exception:
                logging.getLogger(__name__).exception("Maintenance stage failed: %s",name)
                status="failed"
        outcomes[name]=status
        if record:
            record(name,status)
    return outcomes

def run(specs,path):
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS maintenance_status (
            stage TEXT PRIMARY KEY,status TEXT NOT NULL, failures INTEGER NOT NULL, updated TEXT NOT NULL)""")
    def record(name,status):
        with connect(path) as db:
            db.execute("""INSERT INTO maintenance_status VALUES (?,?,?,?)
                ON CONFLICT(stage) DO UPDATE SET status=excluded.status,
                failures=CASE WHEN excluded.status='failed' THEN failures+1 WHEN excluded.status='ok' THEN 0 ELSE failures END,
                updated=excluded.updated""",(name,status,int(status=="failed"),now()))
    def action(module,function):
        def invoke():
            target=getattr(import_module("."+module,__package__),function)
            if module=="thought_tree" and function=="expand":
                from .development_policy import policy
                return target(path,limit=policy(path)["thought_budget"])
            return target(path)
        return invoke
    return execute([(name,action(module,function),deps) for name,module,function,deps in specs],path,record)
