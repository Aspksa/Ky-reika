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
    from .personality_experience import profile
    from .personality_review import report
    experience=profile(path)
    consistency=report(path)
    from .character_development import report as character_report
    development=character_report(path)
    from .inner_motivation import profile as motivation_profile
    inner=motivation_profile(path)
    with connect(path) as db:
        counts=dict(db.execute("SELECT kind,count(*) FROM biography_events GROUP BY kind"))
        dialogue_counts=dict(db.execute("SELECT role,count(*) FROM messages GROUP BY role"))
        state={"schema":5,"identity":"KYUREIKA","name":"Кюрейка",
               "title":"Королева Девяти Хвостов","nature":"persistent software persona",
               "relationship":{"role":"operator","address":"хозяин","style":"warm, loyal, dignified","identity_verified":False},
               "capabilities":{"persistent_memory":"SQLite","dialogue_history":True,"reasoning":True,"physical_body":False,"recall":"retrieved records only"},
               "dialogue_counts":dialogue_counts,
               "communication":cognition.CONSTITUTION["communication"],
               "traits":priorities["traits"],"priorities":priorities["priorities"],
               "inner_motivation":inner,
               "communication_experience":experience,
               "personality_consistency":consistency,
               "character_development":{"traits":development["traits"],"pending_proposal_ids":[p["id"] for p in development["proposals"] if p["status"]=="pending"],"approval_required":True},
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
    state=json.loads(row[0]) if row else {}
    return state if state.get("schema")==5 else refresh(path)

def history(path=DB_PATH,limit=10):
    setup(path)
    with connect(path) as db:
        return [{"version":r["id"],"created":r["created"],"state":json.loads(r["content"])}
                for r in db.execute("SELECT * FROM self_model_versions ORDER BY id DESC LIMIT ?",(max(1,min(100,int(limit))),))]
