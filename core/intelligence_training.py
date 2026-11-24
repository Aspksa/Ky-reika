"""Local recurring assessment; practice priorities do not modify model weights."""
import json
from .database import DB_PATH, connect, now
from .intelligence_benchmark import evaluate

def setup(path):
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS intelligence_training (
            id INTEGER PRIMARY KEY, report TEXT NOT NULL, created TEXT NOT NULL)""")

def refresh(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        previous=db.execute("SELECT id,report FROM intelligence_training ORDER BY id DESC LIMIT 1").fetchone()
        seed=42 if previous is None else 42+previous["id"]
        report=evaluate(seed=seed)
        baseline=evaluate(seed=42)
        report["fixed_benchmark"]=baseline["passed"]
        from .method_experiments import compare
        report["method_experiments"]=compare(seed)
        report["priorities"]=[{"skill":k,"action":"inspect failed cases and validate corrections"} for k in sorted(set(report["weaknesses"]+baseline["weaknesses"]))]
        report["status"]="practice_required" if report["priorities"] else "local_checks_passed"
        db.execute("INSERT INTO intelligence_training(report,created) VALUES (?,?)",(json.dumps(report),now()))
        db.execute("DELETE FROM intelligence_training WHERE id NOT IN (SELECT id FROM intelligence_training ORDER BY id DESC LIMIT 1000)")
    return report

def latest(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        row=db.execute("SELECT report FROM intelligence_training ORDER BY id DESC LIMIT 1").fetchone()
    return json.loads(row["report"]) if row else {}
