"""Shadow comparison telemetry; no automatic production authorization."""
from .database import DB_PATH,connect,now

def record(path,trials):
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS inference_trials (
            id INTEGER PRIMARY KEY,status TEXT NOT NULL,reference_ns INTEGER NOT NULL,
            indexed_ns INTEGER NOT NULL,rules INTEGER NOT NULL,created TEXT NOT NULL)""")
        db.executemany("INSERT INTO inference_trials(status,reference_ns,indexed_ns,rules,created) VALUES (?,?,?,?,?)",
            [(*trial,now()) for trial in trials])
        db.execute("DELETE FROM inference_trials WHERE id NOT IN (SELECT id FROM inference_trials ORDER BY id DESC LIMIT 2000)")

def latest(path=DB_PATH):
    with connect(path) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='inference_trials'").fetchone():
            return {"samples":0,"status":"insufficient_history"}
        rows=db.execute("SELECT * FROM inference_trials ORDER BY id DESC LIMIT 200").fetchall()
    matches=sum(r["status"]=="match" for r in rows)
    failures=len(rows)-matches
    reference=sum(r["reference_ns"] for r in rows)
    indexed=sum(r["indexed_ns"] for r in rows)
    return {"samples":len(rows),"matches":matches,"failures":failures,
            "reference_ns":reference,"indexed_ns":indexed,
            "status":"suspended" if failures else "review_candidate" if len(rows)>=100 and indexed<reference else "insufficient_performance_evidence",
            "limitation":"Repeated workloads and timing noise; compares reachability, not full proof construction.",
            "production_authorized":False}
