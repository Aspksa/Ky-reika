"""Inspect reasoning artifacts, not hidden model thoughts."""
from .database import DB_PATH, connect, now
import json

def assess(context):
    meta=context.get("metalogic",{})
    accepted=meta.get("provisional_deductions",[])
    withheld=meta.get("withheld_deductions",[])
    checks={
        "unsupported_proofs":sum(not d.get("sources") or not d.get("rules") for d in accepted),
        "withheld_proofs":len(withheld),
        "conflicting_values":len(meta.get("conflicts",[])),
        "alternative_paths":sum(len(d.get("alternative_proofs",[])) for d in accepted),
        "confirmed_records":len(context.get("confirmed_knowledge",[]))}
    guidance=[]
    if checks["unsupported_proofs"] or checks["withheld_proofs"] or checks["conflicting_values"]:
        guidance.append("Audit premises and distinguish disputed deductions from supported conclusions.")
    if not checks["confirmed_records"]:
        guidance.append("Identify missing evidence; avoid treating hypotheses as facts.")
    if context.get("abductive_explanations"):
        guidance.append("Compare competing explanations and identify discriminating evidence.")
    checks["disputed_causal_chains"]=sum(c.get("status")=="disputed" for c in context.get("causal_chains",[]))
    checks["creative_hypotheses"]=len(context.get("creative_candidates",[]))
    checks["observed_concept_relations"]=len(context.get("concept_relations",[]))
    checks["strategic_risks"]=sum(len(g.get("risks",[])) for g in context.get("strategic_options",[]))
    if checks["disputed_causal_chains"]:
        guidance.append("Do not rely on disputed causal chains; identify conflicting premises and test alternatives.")
    if checks["creative_hypotheses"] or checks["observed_concept_relations"]:
        guidance.append("Distinguish observed associations and speculative combinations from verified facts; specify a discriminating test.")
    if checks["strategic_risks"]:
        guidance.append("Compare feasible strategic alternatives against actual constraints; do not invent resource estimates.")
    return {"checks":checks,"methods":meta.get("methods",[]),"guidance":guidance,
            "status":"review_required" if guidance else "no_detected_issue",
            "limitation":"Structural diagnostics, not a guarantee of correctness."}

def record(report,path=DB_PATH):
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS metacognitive_reports (
            id INTEGER PRIMARY KEY, content TEXT NOT NULL, created TEXT NOT NULL)""")
        db.execute("INSERT INTO metacognitive_reports(content,created) VALUES (?,?)",
                   (json.dumps(report,ensure_ascii=False),now()))
        db.execute("DELETE FROM metacognitive_reports WHERE id NOT IN (SELECT id FROM metacognitive_reports ORDER BY id DESC LIMIT 1000)")

def apply(strategy,report):
    result=dict(strategy)
    if report["guidance"]:
        result["mode"]="structured"
        result["guidance"]=list(dict.fromkeys(strategy.get("guidance",[])+report["guidance"]))
    return result
