"""Evidence-based diagnostics, not subjective awareness."""
import json
from .database import DB_PATH, connect, now
from . import reasoning, knowledge

def setup(path=DB_PATH):
    reasoning.setup(path)
    knowledge.setup(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS reflection_reports (
            id INTEGER PRIMARY KEY, created TEXT NOT NULL, report TEXT NOT NULL)""")

def inspect(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        counts=dict(db.execute("SELECT level,count(*) FROM cognition_memory GROUP BY level"))
        weak=db.execute("SELECT count(*) FROM cognition_memory WHERE confidence<.6 AND level!='archive'").fetchone()[0]
        disputed=db.execute("SELECT count(*) FROM cognition_memory WHERE contradiction_score>=.5").fetchone()[0]
        pending=db.execute("SELECT count(*) FROM knowledge_versions WHERE status='pending'").fetchone()[0]
        conflicts=db.execute("""SELECT count(*) FROM knowledge_versions p JOIN knowledge_versions c
            ON p.subject=c.subject AND p.predicate=c.predicate
            WHERE p.status='pending' AND c.status='current' AND trim(p.value)!=trim(c.value)""").fetchone()[0]
    recommendations=[]
    if weak:
        recommendations.append("Verify low-confidence memories before relying on them.")
    if disputed or conflicts:
        recommendations.append("Review conflicting evidence without deleting either version.")
    if pending:
        recommendations.append("Review pending knowledge with the user.")
    return {"levels":counts,"low_confidence":weak,"disputed_memories":disputed,
            "pending_knowledge":pending,"potential_conflicts":conflicts,
            "recommendations":recommendations}

def record(path=DB_PATH):
    report=inspect(path)
    with connect(path) as db:
        db.execute("INSERT INTO reflection_reports(created,report) VALUES (?,?)",(now(),json.dumps(report,ensure_ascii=False)))
    return report

def latest(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        row=db.execute("SELECT created,report FROM reflection_reports ORDER BY id DESC LIMIT 1").fetchone()
    return {"created":row["created"],**json.loads(row["report"])} if row else {}
