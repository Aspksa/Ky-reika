"""Background maintenance, not simulated consciousness."""
import logging
from threading import Event, Thread
from .database import DB_PATH, connect, now
from . import cognition, reasoning

def consolidate(path=DB_PATH):
    reasoning.setup(path)
    proposals=cognition.sleep_once(path)
    with connect(path) as db:
        db.execute("""UPDATE memory_links SET weight=min(1,weight+.01)
            WHERE source IN (SELECT id FROM cognition_memory WHERE usage_count>=3 AND level!='archive')
              AND target IN (SELECT id FROM cognition_memory WHERE usage_count>=3 AND level!='archive')""")
        cognition.audit(db,"sleep_completed",{"proposals":proposals})
    from .maintenance_runner import run
    run([
        ("graph","memory_graph","consolidate",()),
        ("reflection","reflection","record",()),
        ("revision","revision","revise",()),
        ("initiative","initiative","generate",()),
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
        ("health","homeostasis","refresh",()),
    ],path)
    return proposals

def start(path=DB_PATH,interval=3600):
    if interval<60:
        raise ValueError("Interval must be at least 60 seconds")
    stop=Event()
    def run():
        delay=0
        while not stop.wait(delay):
            try:
                consolidate(path)
                from .development_policy import policy
                delay=max(60,min(interval,policy(path)['interval']))
            except Exception:
                delay=interval
                logging.getLogger(__name__).exception("Memory maintenance failed")
    worker=Thread(target=run,name="kyureika-memory-maintenance",daemon=True)
    worker.start()
    return stop,worker
