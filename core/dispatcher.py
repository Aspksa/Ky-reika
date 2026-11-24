"""Shared registry for cognitive maintenance; stages remain independently testable."""
from .maintenance_runner import run
STAGES = (
        ("extraction","gateway","process_learning",()),
        ("graph","memory_graph","consolidate",()),
        ("reflection","reflection","record",()),
        ("revision","revision","revise",()),
        
        ("growth","development","grow",()),
        ("rules","rule_validation","refresh",("growth",)),
        ("thoughts","thought_tree","expand",("growth",)),
        ("research","research","refresh",("thoughts",)),
        ("creativity","creativity","generate",("growth",)),
        ("imagination","imagination","refresh",()),
        ("learning","learning_review","refresh",()),
        ("metrics","growth_metrics","snapshot",("thoughts",)),
        ("background","background_reasoning","run",("research",)),
        ("inquiry","deep_inquiry","advance",("background",)),
        ("followups","followup_research","refresh",("inquiry",)),
        ("evidence","followup_execution","run",("followups",)),
        ("synthesis","research_synthesis","refresh",("evidence",)),
        ("theories","theory_memory","refresh",("synthesis",)),
        ("reviews","theory_review","run",("theories",)),
        ("predictions","prediction_checks","refresh",("reviews",)),
        ("lessons","prediction_learning","refresh",("predictions",)),
        ("identity","intellectual_identity","refresh",("lessons",)),
        ("goals","research_goals","refresh",("research",)),
        ("priorities","intellectual_goals","refresh",("goals",)),
        ("discovery","discovery_lab","refresh",()),
        ("theoretical","theoretical_intelligence","refresh",("discovery",)),
        ("world","world_model","refresh",("theoretical",)),
        ("training","intelligence_training","refresh",()),
        ("self","self_model","refresh",("reflection","priorities","identity")),
        ("health","homeostasis","refresh",("revision",)),
        ("initiative","initiative","generate",("reflection","priorities")),

)

def cycle(path):
    return run(STAGES,path)
