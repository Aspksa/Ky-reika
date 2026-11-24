"""Coordinate existing reasoning outputs without promoting hypotheses to facts."""
from collections import defaultdict

def coordinate(message,context):
    from .reasoning import tokens
    terms=tokens(message)
    methods=["epistemic","deductive"]
    triggers={"causal":{"why","почему","причина"},"counterfactual":{"если","if","бы"},
              "temporal":{"когда","раньше","when","before"},
              "analogical":{"похож","аналогия","similar"},
              "normative":{"можно","нужно","allowed","must"}}
    for method,words in triggers.items():
        if terms & words:
            methods.append(method)
    if context.get("inductive_patterns"):
        methods.append("inductive")
    if context.get("abductive_explanations"):
        methods.append("abductive")
    groups=defaultdict(set)
    for f in context.get("confirmed_knowledge",[]):
        groups[(f["subject"],f["predicate"])].add(f["value"])
    deductions=context.get("derived_hypotheses",[])
    for d in deductions:
        s,p,v=d["conclusion"]
        groups[(s,p)].add(v)
    conflicts=[{"subject":s,"predicate":p,"values":sorted(values)}
               for (s,p),values in groups.items() if len(values)>1]
    accepted=[]
    withheld=[]
    for d in deductions:
        s,p,v=d["conclusion"]
        target=withheld if d.get("conflicts_with_confirmed") or len(groups[(s,p)])>1 else accepted
        target.append(d)
    disputed=bool(conflicts or withheld or context.get("potential_conflicts"))
    stale=context.get("deduction_audit",{}).get("stale_records",[])
    if disputed:
        methods.extend(["paraconsistent","dialectical"])
    if stale:
        methods.append("revision")
    return {"methods":methods,"provisional_deductions":accepted,
            "withheld_deductions":withheld,"conflicts":conflicts,
            "status":"review_required" if disputed or stale else "provisional" if accepted or context.get("confirmed_knowledge") else "insufficient_evidence",
            "guidance":"Methods are recommendations, not executed simulations. Never treat withheld deductions or hypotheses as established facts. Preserve external-action restrictions."}
