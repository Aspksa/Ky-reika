"""Observable development metrics, not IQ or consciousness measurements."""
import json
from .database import DB_PATH, connect, now

def snapshot(path=DB_PATH):
    from .thought_tree import setup
    from .adaptation import setup as adaptation_setup
    from .revision import setup as revision_setup
    setup(path)
    adaptation_setup(path)
    revision_setup(path)
    with connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS growth_snapshots (id INTEGER PRIMARY KEY, created TEXT NOT NULL, metrics TEXT NOT NULL)")
        queries={
            "confirmed_facts":"SELECT count(*) FROM knowledge_versions WHERE status='current'",
            "active_hypotheses":"SELECT count(*) FROM development_thoughts WHERE status='candidate'",
            "rule_candidates":"SELECT count(*) FROM development_thoughts WHERE status='candidate' AND kind='rule'",
            "thought_steps":"SELECT count(*) FROM thought_nodes",
            "withdrawn_deductions":"SELECT count(*) FROM deduction_history WHERE withdrawn IS NOT NULL",
            "feedback_count":"SELECT count(*) FROM response_feedback",
            "mean_feedback":"SELECT avg(rating) FROM response_feedback",
            "tracked_responses":"SELECT count(*) FROM strategy_usage"}
        metrics={k:db.execute(q).fetchone()[0] for k,q in queries.items()}
        db.execute("INSERT INTO growth_snapshots(created,metrics) VALUES (?,?)",(now(),json.dumps(metrics)))
        db.execute("DELETE FROM growth_snapshots WHERE id NOT IN (SELECT id FROM growth_snapshots ORDER BY id DESC LIMIT 2160)")
    return metrics

def latest(path=DB_PATH):
    from .database import initialize
    initialize(path)
    with connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS growth_snapshots (id INTEGER PRIMARY KEY, created TEXT NOT NULL, metrics TEXT NOT NULL)")
        rows=list(db.execute("SELECT * FROM growth_snapshots ORDER BY id DESC LIMIT 24"))
    if not rows:
        return {}
    current=json.loads(rows[0]["metrics"])
    baseline=json.loads(rows[-1]["metrics"])
    return {"created":rows[0]["created"],"metrics":current,"baseline":rows[-1]["created"],
            "changes":{k:v-baseline[k] for k,v in current.items() if v is not None and baseline.get(k) is not None},
            "guidance":"Counts measure activity, not intelligence or verified improvement."}
