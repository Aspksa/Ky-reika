"""Bounded background development; proposals never become facts automatically."""
import json
import hashlib
from .database import DB_PATH, connect, now
from .hypotheses import analyze
from .revision import audit

def setup(path=DB_PATH):
    from .inference import setup as init
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS development_thoughts (
            fingerprint TEXT PRIMARY KEY, kind TEXT NOT NULL, content TEXT NOT NULL,
            status TEXT NOT NULL, created TEXT NOT NULL, updated TEXT NOT NULL,
            observations INTEGER NOT NULL DEFAULT 1)""")

def grow(path=DB_PATH):
    setup(path)
    hypotheses=analyze(path)
    candidates=[("pattern",p) for p in hypotheses["patterns"]]+[("explanation",e) for e in hypotheses["explanations"]]
    active=set()
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        for kind,item in candidates[:100]:
            content=json.dumps(item,ensure_ascii=False,sort_keys=True)
            identity=[kind,item["predicate"],item["value"]] if kind=="pattern" else [kind,item["observation"],item["rule"]]
            key=hashlib.sha256(json.dumps(identity,ensure_ascii=False).encode()).hexdigest()
            active.add(key)
            db.execute("""INSERT INTO development_thoughts(fingerprint,kind,content,status,created,updated)
                VALUES (?,?,?,'candidate',?,?) ON CONFLICT(fingerprint) DO UPDATE SET
                observations=observations+CASE WHEN content!=excluded.content THEN 1 ELSE 0 END,
                content=excluded.content,status='candidate',updated=excluded.updated""",(key,kind,content,now(),now()))
        for row in db.execute("SELECT fingerprint FROM development_thoughts WHERE status='candidate'").fetchall():
            if row[0] not in active:
                db.execute("UPDATE development_thoughts SET status='inactive',updated=? WHERE fingerprint=?",(now(),row[0]))
    return {"active_candidates":len(active),"deduction_review":audit(path)}

def recent(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        return [{"kind":r["kind"],"hypothesis":json.loads(r["content"]),"evidence_revisions":r["observations"]}
                for r in db.execute("SELECT * FROM development_thoughts WHERE status='candidate' ORDER BY updated DESC LIMIT 5")]
