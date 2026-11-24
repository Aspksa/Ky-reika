"""Read-only research ledger; stored reviews are not independent proof."""
import json

def report(db,tables):
    result={"goals":[],"theories":[],"predictions":[],"hypotheses":[],"counts":{}}
    specs={"goals":"research_goals","theories":"theory_versions","predictions":"prediction_checks","hypotheses":"discovery_predictions"}
    for key,table in specs.items():
        result["counts"][key]=db.execute("SELECT count(*) FROM "+table).fetchone()[0] if table in tables else None
    if "research_goals" in tables:
        result["goals"]=[dict(r) for r in db.execute("SELECT question,priority,status,updated,revision FROM research_goals WHERE status!='superseded' ORDER BY priority DESC,root LIMIT 30")]
    if "theory_versions" in tables:
        for r in db.execute("SELECT t.* FROM theory_versions t JOIN (SELECT id,max(revision) revision FROM theory_versions GROUP BY id) v ON t.id=v.id AND t.revision=v.revision ORDER BY t.created DESC LIMIT 20"):
            data=json.loads(r["content"])
            result["theories"].append({"revision":r["revision"],"created":r["created"],"status":data.get("status"),"questions":data.get("questions"),"next_test":data.get("next_test")})
    if "prediction_checks" in tables:
        for r in db.execute("SELECT * FROM prediction_checks ORDER BY updated DESC LIMIT 30"):
            data=json.loads(r["content"])
            result["predictions"].append({"observable":data.get("observable"),"status":data.get("status"),"sources":data.get("sources"),"updated":r["updated"]})
    if "discovery_predictions" in tables:
        for r in db.execute("SELECT * FROM discovery_predictions ORDER BY created DESC LIMIT 30"):
            candidate=json.loads(r["candidate"])
            sources=json.loads(r["sources"])
            status="awaiting_evidence"
            if "knowledge_versions" in tables:
                valid=all(db.execute("SELECT 1 FROM knowledge_versions WHERE id=? AND status='current'",(i,)).fetchone() for i in sources)
                observed=db.execute("SELECT id,value FROM knowledge_versions WHERE subject=? AND predicate=? AND status='current'",tuple(candidate[:2])).fetchone()
                if not valid: status="premises_superseded"
                elif observed and observed["id"]>r["cutoff"]: status="observed_match" if observed["value"]==candidate[2] else "observed_counterexample"
                elif observed: status="preexisting_observation"
            result["hypotheses"].append({"candidate":candidate,"sources":sources,"status":status,"created":r["created"]})
    return result
