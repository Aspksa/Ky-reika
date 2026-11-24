"""Read-only operational diagnostics, excluding dialogue and credentials."""
from .database import DB_PATH, connect
from .cognitive_bus import snapshot

def report(path=DB_PATH):
    events=snapshot(path)
    with connect(path) as db:
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        stages=[dict(r) for r in db.execute("SELECT * FROM maintenance_status ORDER BY stage")] if "maintenance_status" in tables else []
        jobs=dict(db.execute("SELECT status,count(*) FROM background_jobs GROUP BY status")) if "background_jobs" in tables else {}
    return {"events":events,"stages":stages,"jobs":jobs,"external_actions":"propose_only"}
