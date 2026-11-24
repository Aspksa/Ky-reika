"""Epistemic audit: recorded confidence is not calibrated truth probability."""
def assess(context):
    facts=context.get("confirmed_knowledge",[])
    conflicts=context.get("potential_conflicts",[])
    disputed={r.get("current_id") for r in conflicts}
    records=[]
    for f in facts:
        issues=[]
        if not f.get("source","").strip():
            issues.append("missing_provenance")
        if f.get("confidence",0)<.6:
            issues.append("low_recorded_confidence")
        if f.get("id") in disputed:
            issues.append("pending_conflicting_claim")
        records.append({"id":f.get("id"),"issues":issues,
            "status":"review_required" if issues else "recorded_confirmation",
            "independent_verification":"not_established"})
    guidance=[]
    if not facts:
        guidance.append("Distinguish missing local evidence from evidence of absence.")
    if any(r["issues"] for r in records):
        guidance.append("Qualify disputed or weakly sourced records; seek corroboration.")
    if context.get("derived_hypotheses") or context.get("theoretical_comparisons"):
        guidance.append("Keep conditional deductions and provisional theories separate from confirmed records.")
    return {"records":records,"guidance":guidance,"limitation":"Local provenance audit, not external source verification."}

def apply(strategy,report):
    result=dict(strategy)
    if report["guidance"]:
        result["guidance"]=list(dict.fromkeys([*strategy.get("guidance",[]),*report["guidance"]]))
    return result
