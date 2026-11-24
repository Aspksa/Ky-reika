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
    from .memory_graph import consolidate as consolidate_graph
    consolidate_graph(path)
    from .reflection import record
    record(path)
    from .revision import revise
    revise(path)
    from .initiative import generate
    generate(path)
    from .development import grow
    grow(path)
    from .rule_validation import refresh as validate_rules
    validate_rules(path)
    from .thought_tree import expand
    from .development_policy import policy
    expand(path,limit=policy(path)['thought_budget'])
    from .research import refresh
    refresh(path)
    from .creativity import generate as generate_ideas
    generate_ideas(path)
    from .growth_metrics import snapshot
    from .imagination import refresh as imagine
    imagine(path)
    from .learning_review import refresh as review_learning
    review_learning(path)
    snapshot(path)
    from .self_model import refresh as refresh_self
    refresh_self(path)
    from .background_reasoning import run as background_review
    background_review(path)
    from .deep_inquiry import advance
    advance(path)
    from .followup_research import refresh as refresh_followups
    refresh_followups(path)
    from .followup_execution import run as execute_followups
    execute_followups(path)
    from .research_goals import refresh as refresh_goals
    refresh_goals(path)
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
