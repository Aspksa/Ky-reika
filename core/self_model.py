"""Versioned software persona model, not subjective experience."""
import json
from .database import DB_PATH, connect, now
from . import cognition, biography, motivation

def setup(path=DB_PATH):
    biography.setup(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS self_model_versions (
            id INTEGER PRIMARY KEY, content TEXT NOT NULL, created TEXT NOT NULL)""")

def refresh(path=DB_PATH):
    setup(path)
    priorities=motivation.evaluate(path)
    events=biography.timeline(path,12)
    with connect(path) as db:
        counts=dict(db.execute("SELECT kind,count(*) FROM biography_events GROUP BY kind"))
        state={"identity":"KYUREIKA","nature":"fictional software persona",
               "traits":priorities["traits"],"priorities":priorities["priorities"],
               "experience_counts":counts,"biography_event_ids":[e["id"] for e in events],
               "autonomy":"propose_only"}
        content=json.dumps(state,ensure_ascii=False,sort_keys=True)
        previous=db.execute("SELECT content FROM self_model_versions ORDER BY id DESC LIMIT 1").fetchone()
        if previous is None or previous[0]!=content:
            db.execute("INSERT INTO self_model_versions(content,created) VALUES (?,?)",(content,now()))
        return state

def current(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        row=db.execute("SELECT content FROM self_model_versions ORDER BY id DESC LIMIT 1").fetchone()
    return json.loads(row[0]) if row else refresh(path)

def history(path=DB_PATH,limit=10):
    setup(path)
    with connect(path) as db:
        return [{"version":r["id"],"created":r["created"],"state":json.loads(r["content"])}
                for r in db.execute("SELECT * FROM self_model_versions ORDER BY id DESC LIMIT ?",(max(1,min(100,int(limit))),))]
