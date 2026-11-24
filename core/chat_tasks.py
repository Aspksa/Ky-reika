"""Durable operator requests for allowlisted local maintenance."""
from . import job_queue
from .database import connect
from importlib import import_module

ACTIONS={
    "learning":("learning_review","refresh"),
    "research":("research_goals","refresh"),
    "memory":("memory_graph","consolidate"),
}
SCOPE="local-v1"

def enqueue(path,name):
    if name not in ACTIONS:
        raise ValueError("Unknown maintenance request")
    return job_queue.enqueue(path,"chat_task",name,SCOPE)

def process(path):
    job=job_queue.claim(path,"chat_task",SCOPE)
    if job is None:
        return
    success=False
    try:
        module,function=ACTIONS[job["payload"]]
        getattr(import_module("."+module,__package__),function)(path)
        success=True
    finally:
        job_queue.finish(path,job,success)

def recent(path):
    job_queue.setup(path)
    with connect(path) as db:
        return [dict(r) for r in db.execute("SELECT id,status,attempts FROM background_jobs WHERE kind='chat_task' AND scope=? ORDER BY id DESC LIMIT 20",(SCOPE,))]
