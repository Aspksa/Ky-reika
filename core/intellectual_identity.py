"""Descriptive cognitive habits, not claims of consciousness or competence."""
import json
from .database import DB_PATH, connect, now
from .inquiry_learning import profile
from .prediction_learning import profile as prediction_profile

def describe(stats):
    total=sum(v["samples"] for v in stats.values())
    dominant=max(sorted(stats),key=lambda m:stats[m]["samples"]) if total>=20 else None
    if dominant and stats[dominant]["samples"]/total<.4:
        dominant=None
    return {"observed_rounds":total,"dominant_method":dominant,
            "methods":stats,"status":"observational" if total>=20 else "insufficient_history"}

def refresh(path=DB_PATH):
    state=describe(profile(path))
    predictions=prediction_profile(path)
    state["evaluated_predictions"]=predictions["evaluated"]
    state["observed_match_rate"]=predictions["observed_match_rate"]
    state["limitation"]="Method frequency and novelty do not establish correctness or stable personality."
    content=json.dumps(state,sort_keys=True,ensure_ascii=False)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS intellectual_identity_versions (
            id INTEGER PRIMARY KEY, content TEXT NOT NULL, created TEXT NOT NULL)""")
        db.execute("BEGIN IMMEDIATE")
        old=db.execute("SELECT content FROM intellectual_identity_versions ORDER BY id DESC LIMIT 1").fetchone()
        if not old or old[0]!=content:
            db.execute("INSERT INTO intellectual_identity_versions(content,created) VALUES (?,?)",(content,now()))
    return state

def current(path=DB_PATH):
    with connect(path) as db:
        if db.execute("SELECT 1 FROM sqlite_master WHERE name='intellectual_identity_versions'").fetchone():
            row=db.execute("SELECT content FROM intellectual_identity_versions ORDER BY id DESC LIMIT 1").fetchone()
            if row:
                return json.loads(row[0])
    return describe({})
