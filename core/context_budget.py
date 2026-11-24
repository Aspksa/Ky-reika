"""Select cloud context without mutating local knowledge or evidence."""
import json
import re

CORE=("dialogue_style","constitution","policy","self_model","affect","strategy","integral_intelligence",
      "confirmed_knowledge","potential_conflicts","metalogic","epistemic_audit",
      "uncertainty","memory","recent_dialogue","cognitive_integrity")
METHOD_FIELDS={
    "causal":("causal_chains","knowledge_chronology"),
    "abstraction":("concepts","concept_relations"),
    "strategic":("active_intentions","goal_progress","next_plan_steps","strategic_options"),
    "creative":("creative_candidates","creative_ideas"),
    "abductive":("abductive_explanations",),
    "evidence_audit":("evidence_states","deduction_audit","correction_tasks"),
    "integrity_review":("cognitive_health","deduction_audit"),
}
def select(message,context):
    plan=context.get("integral_intelligence",{})
    selected={k:context[k] for k in CORE if k in context}
    for method in plan.get("methods",[]):
        for key in METHOD_FIELDS.get(method.get("method") if isinstance(method,dict) else method,()):
            if key in context:
                selected[key]=context[key]
    terms=set(re.findall(r"\w+",message.casefold()))
    budget=48000 if plan.get("depth")=="deep" else 24000
    size=lambda obj:len(json.dumps(obj,ensure_ascii=False).encode("utf-8"))
    for key,value in context.items():
        if key in selected or key=="message" or not value:
            continue
        words=set(re.findall(r"\w+",json.dumps(value,ensure_ascii=False).casefold()))
        if terms & words and size(selected)+size({key:value})<=budget:
            selected[key]=value
    selected["context_scope"]={"omitted_sections":sorted(set(context)-set(selected)-{"message"}),"limitation":"Selected context is not the complete local knowledge base; omitted evidence is not evidence of absence."}
    return selected
