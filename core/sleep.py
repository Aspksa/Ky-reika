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
    from .dispatcher import cycle
    cycle(path)
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
