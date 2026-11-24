"""Transactional change counters; no message contents or credentials."""
from .database import connect

TABLES={"messages":"dialogue","memories":"memory","knowledge_versions":"knowledge",
        "response_feedback":"feedback","personality":"personality",
        "research_goals":"research","background_reviews":"research",
        "prediction_checks":"research"}

def install(path):
    with connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS cognitive_events (topic TEXT PRIMARY KEY, revision INTEGER NOT NULL)")
        existing={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table,topic in TABLES.items():
            if table not in existing:
                continue
            for op in ("INSERT","UPDATE","DELETE"):
                db.execute(f"""CREATE TRIGGER IF NOT EXISTS bus_{table}_{op} AFTER {op} ON {table}
                    BEGIN INSERT INTO cognitive_events VALUES ('{topic}',1)
                    ON CONFLICT(topic) DO UPDATE SET revision=revision+1; END""")

def snapshot(path):
    install(path)
    with connect(path) as db:
        return dict(db.execute("SELECT topic,revision FROM cognitive_events"))
