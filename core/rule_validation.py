"""Revalidate learned associations without promoting them to deductive laws."""
import json
import hashlib
from .database import DB_PATH, connect, now
from .rule_learning import discover
from .knowledge import setup as init

def setup(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS rule_assessments (
            fingerprint TEXT NOT NULL, revision INTEGER NOT NULL,
            content TEXT NOT NULL, created TEXT NOT NULL,
            PRIMARY KEY(fingerprint,revision))""")

def assess(rule):
    support=rule["validation_support"]
    opposition=rule["counterexamples"]
    return "counterexample_found" if opposition else "provisionally_supported" if len(support)>=3 else "insufficient_evidence"

def refresh(path=DB_PATH):
    setup(path)
    candidates=discover(path)
    active={}
    for rule in candidates:
        key=hashlib.sha256(json.dumps([rule["premise"],rule["conclusion"]],sort_keys=True).encode()).hexdigest()
        active[key]={**rule,"assessment":assess(rule),"deductive_authority":False}
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        previous={r["fingerprint"]:r for r in db.execute("""SELECT a.* FROM rule_assessments a
            JOIN (SELECT fingerprint,max(revision) AS revision FROM rule_assessments GROUP BY fingerprint) b
            ON a.fingerprint=b.fingerprint AND a.revision=b.revision""")}
        for key,r in previous.items():
            if key not in active:
                old=json.loads(r["content"])
                active[key]={"premise":old["premise"],"conclusion":old["conclusion"],
                    "assessment":"no_longer_candidate","deductive_authority":False}
        for key,state in active.items():
            content=json.dumps(state,sort_keys=True,ensure_ascii=False)
            old=previous.get(key)
            if old is None or old["content"]!=content:
                db.execute("INSERT INTO rule_assessments VALUES (?,?,?,?)",
                    (key,old["revision"]+1 if old else 1,content,now()))
    return len(candidates)

def recent(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        return [{"revision":r["revision"],**json.loads(r["content"])} for r in db.execute("""SELECT a.* FROM rule_assessments a
            JOIN (SELECT fingerprint,max(revision) AS revision FROM rule_assessments GROUP BY fingerprint) b
            ON a.fingerprint=b.fingerprint AND a.revision=b.revision
            ORDER BY a.created DESC LIMIT 8""")]
