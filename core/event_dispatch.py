"""Persistent acknowledgements for idempotent, event-driven maintenance."""
import json
from .database import connect
from .cognitive_bus import snapshot

def run_if_changed(path,stage,topics,action):
    revisions=snapshot(path)
    stamp=json.dumps({"version":2,"inputs":{topic:revisions.get(topic,0) for topic in topics}},sort_keys=True)
    with connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS cognitive_ack (stage TEXT PRIMARY KEY, stamp TEXT NOT NULL)")
        previous=db.execute("SELECT stamp FROM cognitive_ack WHERE stage=?",(stage,)).fetchone()
    if previous and previous[0]==stamp:
        return False
    action()
    # Acknowledge only the input revisions seen before execution.
    with connect(path) as db:
        db.execute("INSERT INTO cognitive_ack VALUES (?,?) ON CONFLICT(stage) DO UPDATE SET stamp=excluded.stamp",(stage,stamp))
    return True
