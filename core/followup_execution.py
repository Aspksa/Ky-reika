"""Autonomous local evidence retrieval for generated questions."""
import json
from .database import DB_PATH, connect, now
from .followup_research import setup as init
from .knowledge import setup as knowledge_setup
from .reasoning import tokens

def setup(path=DB_PATH):
    init(path)
    knowledge_setup(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS followup_results (
            question_id TEXT PRIMARY KEY REFERENCES followup_questions(id),
            evidence TEXT NOT NULL, updated TEXT NOT NULL)""")

def run(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        facts=[dict(r) for r in db.execute("""SELECT id,subject,predicate,value,source,confidence
            FROM knowledge_versions WHERE status='current' ORDER BY id DESC LIMIT 2000""")]
        questions=list(db.execute("""SELECT q.* FROM followup_questions q
            JOIN development_thoughts d ON d.fingerprint=q.root AND d.observations=q.revision
            LEFT JOIN followup_results r ON r.question_id=q.id
            WHERE q.status='awaiting_evidence' AND d.status='candidate'
            ORDER BY r.updated IS NOT NULL,r.updated,q.id LIMIT 10"""))
        for q in questions:
            terms=tokens(q["question"])
            scored=[]
            for f in facts:
                words=tokens(f["subject"]+" "+f["predicate"]+" "+f["value"])
                score=len(terms & words)/max(1,len(terms | words))
                if score>=.1:
                    scored.append((score,f))
            evidence=[f for _,f in sorted(scored,key=lambda x:x[0],reverse=True)[:8]]
            db.execute("""INSERT INTO followup_results VALUES (?,?,?)
                ON CONFLICT(question_id) DO UPDATE SET evidence=excluded.evidence,updated=excluded.updated""",
                (q["id"],json.dumps(evidence,ensure_ascii=False),now()))
        return len(questions)

def recent(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        result=[]
        for r in db.execute("""SELECT q.question,r.evidence FROM followup_results r
            JOIN followup_questions q ON q.id=r.question_id
            JOIN development_thoughts d ON d.fingerprint=q.root AND d.observations=q.revision
            WHERE q.status='awaiting_evidence' AND d.status='candidate' ORDER BY r.updated DESC LIMIT 5"""):
            evidence=[f for f in json.loads(r["evidence"]) if db.execute(
                "SELECT 1 FROM knowledge_versions WHERE id=? AND status='current'",(f["id"],)).fetchone()]
            result.append({"question":r["question"],"evidence":evidence,
                "status":"candidate_evidence" if evidence else "no_matching_evidence",
                "limitation":"Lexical relevance is not proof."})
        return result
