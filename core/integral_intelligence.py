"""Route intellectual methods by task and evidence; no daily request quota."""
import re

def coordinate(message,context):
    words=set(re.findall(r"\w+",message.casefold()))
    methods=[]
    def add(name,reason):
        methods.append({"method":name,"reason":reason})
    if context.get("potential_conflicts") or context.get("metalogic",{}).get("conflicts"):
        add("evidence_audit","conflicting evidence")
    if context.get("causal_chains") or words & {"почему","причина","последствия","why","cause"}:
        add("causal","causal question or relevant chains")
    if context.get("concept_relations") or context.get("concepts"):
        add("abstraction","relevant observed concepts")
    if words & {"план","стратегия","plan","strategy","сравни","compare"}:
        add("strategic","planning or comparison")
    if words & {"придумай","идея","идеи","invent","brainstorm"}:
        add("creative","explicit creative task")
    if context.get("abductive_explanations"):
        add("abductive","competing explanations")
    if not methods:
        add("direct","no specific method signal")
    structured=context.get("strategy",{}).get("mode")=="structured"
    deep=any(m["method"] in ("evidence_audit","causal","strategic","abductive") for m in methods)
    plan={"methods":methods,"depth":"deep" if deep or (structured and len(methods)>1) else "focused" if structured or methods[0]["method"]!="direct" else "direct",
            "guidance":"Combine selected methods only when relevant. Distinguish evidence, deductions and hypotheses. Method selection is heuristic, not measured intelligence.",
            "external_actions":"propose_only"}

    from .targeted_practice import adapt
    return adapt(plan,context.get("intelligence_training",{}))
