"""Research questions derived from inquiry history, never promoted to facts."""
import json
import hashlib
from .database import DB_PATH, connect, now
from .deep_inquiry import setup as init
from .reasoning import tokens

def setup(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS followup_questions (
            id TEXT PRIMARY KEY, root TEXT NOT NULL, revision INTEGER NOT NULL,
            question TEXT NOT NULL, source_round INTEGER NOT NULL, related TEXT NOT NULL,
            status TEXT NOT NULL, updated TEXT NOT NULL)""")

def refresh(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""UPDATE followup_questions SET status='superseded' WHERE NOT EXISTS (
            SELECT 1 FROM development_thoughts d WHERE d.fingerprint=followup_questions.root
            AND d.observations=followup_questions.revision AND d.status='candidate')""")
        rows=list(db.execute("""SELECT i.* FROM deep_inquiry i JOIN development_thoughts d
            ON d.fingerprint=i.root AND d.observations=i.revision
            WHERE d.status='candidate' AND i.status IN ('unverified','awaiting_evidence')
            ORDER BY i.created DESC LIMIT 100"""))
        for r in rows:
            question=json.loads(r["content"]).get("next_test","").strip()
            if not question:
                continue
            normalized=" ".join(question.casefold().split())
            key=hashlib.sha256(json.dumps([r["root"],r["revision"],normalized]).encode()).hexdigest()
            terms=tokens(question)
            related=[]
            for other in rows:
                if other["root"]==r["root"]:
                    continue
                q=json.loads(other["content"]).get("next_test","")
                words=tokens(q)
                score=len(terms & words)/max(1,len(terms | words))
                if score>=.3:
                    related.append({"root":other["root"],"revision":other["revision"],"round":other["round"],"similarity":score})
            related=sorted(related,key=lambda x:x["similarity"],reverse=True)[:5]
            db.execute("""INSERT OR IGNORE INTO followup_questions VALUES (?,?,?,?,?,?,?,?)""",
                (key,r["root"],r["revision"],question,r["round"],json.dumps(related),"awaiting_evidence",now()))
def recent(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        return [{**dict(r),"related":json.loads(r["related"])} for r in db.execute("""SELECT q.* FROM followup_questions q
            JOIN development_thoughts d ON d.fingerprint=q.root AND d.observations=q.revision
            WHERE q.status='awaiting_evidence' AND d.status='candidate' ORDER BY q.updated DESC LIMIT 5""")]
