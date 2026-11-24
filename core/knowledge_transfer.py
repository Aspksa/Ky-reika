"""Transfer methods, not factual conclusions, between tasks."""
from .reasoning import tokens

def suggest(message,context):
    terms=tokens(message)
    methods=set(context.get("metalogic",{}).get("methods",[]))
    result=[]
    for lesson in context.get("prediction_learning",{}).get("lessons",[]):
        if lesson["status"]=="awaiting_observation" or not lesson.get("sources"):
            continue
        subject,predicate,value=lesson["observable"]
        overlap=terms & tokens(" ".join((subject,predicate,value)))
        if not overlap and not methods.intersection({"causal","counterfactual","inductive","abductive"}):
            continue
        result.append({"origin":[lesson["id"],lesson["revision"]],
            "source_ids":lesson["sources"],"original_observation":lesson["observable"],
            "method":lesson["guidance"],"match":"lexical" if overlap else "method_only",
            "shared_terms":sorted(overlap),"status":"transfer_candidate",
            "required_test":"Check target assumptions and obtain independent target evidence.",
            "factual_transfer_authorized":False})
    return sorted(result,key=lambda r:(-len(r["shared_terms"]),r["origin"]))[:5]
