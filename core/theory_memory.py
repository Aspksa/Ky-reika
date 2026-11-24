"""Versioned research frameworks, never automatically confirmed theories."""
import hashlib
import json
from .database import DB_PATH, connect, now
from .research_synthesis import recent as syntheses

def refresh(path=DB_PATH):
    candidates=syntheses(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""CREATE TABLE IF NOT EXISTS theory_versions (
            id TEXT NOT NULL, revision INTEGER NOT NULL, content TEXT NOT NULL,
            created TEXT NOT NULL, PRIMARY KEY(id,revision))""")
        previous={r["id"]:r for r in db.execute("""SELECT t.* FROM theory_versions t
            JOIN (SELECT id,max(revision) revision FROM theory_versions GROUP BY id) v
            ON t.id=v.id AND t.revision=v.revision""")}
        active={}
        for item in candidates:
            key=hashlib.sha256(json.dumps(sorted(item["question_ids"])).encode()).hexdigest()
            active[key]={**item,"status":"unverified_framework",
                "competing_explanations":["Common underlying relationship","Coincidental overlap","Shared retrieval bias"],
                "counterexamples":[],"counterexample_status":"not_tested",
                "next_test":item["next_test"]}
        for key,row in previous.items():
            if key not in active:
                active[key]={**json.loads(row["content"]),"status":"inactive_not_currently_selected"}
        for key,item in active.items():
            content=json.dumps(item,sort_keys=True,ensure_ascii=False)
            old=previous.get(key)
            if not old or old["content"]!=content:
                db.execute("INSERT INTO theory_versions VALUES (?,?,?,?)",
                    (key,old["revision"]+1 if old else 1,content,now()))
        return len(candidates)

def recent(path=DB_PATH):
    valid={tuple(sorted(s["question_ids"])):s for s in syntheses(path)}
    with connect(path) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='theory_versions'").fetchone():
            return []
        result=[]
        for r in db.execute("""SELECT t.* FROM theory_versions t JOIN
            (SELECT id,max(revision) revision FROM theory_versions GROUP BY id) v
            ON t.id=v.id AND t.revision=v.revision ORDER BY t.created DESC"""):
            item=json.loads(r["content"])
            source=valid.get(tuple(sorted(item["question_ids"])))
            if item["status"]=="unverified_framework" and source and all(item[k]==source[k] for k in ("shared_sources","distinct_sources","questions")):
                result.append({"id":r["id"],"revision":r["revision"],**item})
        return result[:5]
