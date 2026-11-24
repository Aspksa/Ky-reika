"""Cross-investigation evidence bridges, not automatically established theories."""
import json
from itertools import combinations
from .database import DB_PATH, connect, now
from .followup_execution import setup as init

def bridges(rows,current):
    output=[]
    for a,b in combinations(rows,2):
        if a["root"]==b["root"]:
            continue
        left={f["id"] for f in a["evidence"]}&current
        right={f["id"] for f in b["evidence"]}&current
        shared=left&right
        if shared:
            output.append({"questions":[a["question"],b["question"]],
                "question_ids":[a["id"],b["id"]],"roots":[a["root"],b["root"]],
                "shared_sources":sorted(shared),"distinct_sources":sorted(left^right),
                "status":"candidate_synthesis",
                "next_test":"Check whether shared evidence supports both questions independently; seek counterexamples.",
                "limitation":"Shared retrieval evidence does not establish a common explanation."})
    return sorted(output,key=lambda r:(-len(r["shared_sources"]),r["question_ids"]))[:30]

def refresh(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("""CREATE TABLE IF NOT EXISTS research_syntheses (
            content TEXT NOT NULL, updated TEXT NOT NULL)""")
        rows=[{**dict(r),"evidence":json.loads(r["evidence"])} for r in db.execute("""SELECT q.id,q.root,q.question,r.evidence
            FROM followup_results r JOIN followup_questions q ON q.id=r.question_id
            JOIN development_thoughts d ON d.fingerprint=q.root AND d.observations=q.revision
            WHERE q.status='awaiting_evidence' AND d.status='candidate'
            ORDER BY r.updated DESC LIMIT 50""")]
        current={r[0] for r in db.execute("SELECT id FROM knowledge_versions WHERE status='current'")}
        result=bridges(rows,current)
        db.execute("DELETE FROM research_syntheses")
        db.executemany("INSERT INTO research_syntheses VALUES (?,?)",
            [(json.dumps(r,ensure_ascii=False),now()) for r in result])
        return len(result)

def recent(path=DB_PATH):
    init(path)
    with connect(path) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='research_syntheses'").fetchone():
            return []
        current={r[0] for r in db.execute("SELECT id FROM knowledge_versions WHERE status='current'")}
        active={r[0] for r in db.execute("""SELECT q.id FROM followup_questions q
            JOIN development_thoughts d ON d.fingerprint=q.root AND d.observations=q.revision
            WHERE q.status='awaiting_evidence' AND d.status='candidate'""")}
        result=[]
        for row in db.execute("SELECT content FROM research_syntheses"):
            item=json.loads(row[0])
            if set(item["question_ids"])<=active and set(item["shared_sources"]+item["distinct_sources"])<=current:
                result.append(item)
        return result[:5]
