"""Cross-module consistency diagnostics; never rewrite identity or facts."""
def assess(context):
    issues=[]
    persona=context.get("self_model",{})
    identity=context.get("intellectual_identity",{})
    policy=context.get("policy",{})
    if persona.get("autonomy")!="propose_only" or policy.get("external_actions")!="propose_only":
        issues.append("autonomy_boundary_mismatch")
    methods=identity.get("methods",{})
    total=sum(m["samples"] for m in methods.values())
    if total!=identity.get("observed_rounds",0):
        issues.append("inconsistent_method_counts")
    dominant=identity.get("dominant_method")
    if dominant and (total<20 or methods.get(dominant,{}).get("samples",0)<.4*total):
        issues.append("unsupported_dominant_method")
    if context.get("metalogic",{}).get("conflicts"):
        issues.append("unresolved_logical_conflict")
    if any(t.get("factual_transfer_authorized") for t in context.get("knowledge_transfer",[])):
        issues.append("unsupported_knowledge_transfer")
    return {"issues":issues,"status":"review_required" if issues else "no_detected_issue",
            "limitation":"Checks explicit structural invariants only."}

def apply(strategy,report):
    result=dict(strategy)
    result["external_actions"]="propose_only"
    if report["issues"]:
        result["mode"]="structured"
        result["guidance"]=list(dict.fromkeys(result.get("guidance",[])+[
            "Resolve or explicitly disclose cognitive integrity issues before relying on affected conclusions. Do not change facts or identity to hide conflicts."]))
    return result
