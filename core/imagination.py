"""Read-only counterfactual experiments, not predictions."""
import json
from .database import DB_PATH, connect, now
from .scenarios import simulate
from .inference import setup as init, triple

def setup(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS imagined_worlds (
            assumption TEXT PRIMARY KEY, result TEXT NOT NULL, updated TEXT NOT NULL)""")

def refresh(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        facts={triple((r["subject"],r["predicate"],r["value"])):r["id"]
               for r in db.execute("SELECT * FROM knowledge_versions WHERE status='current'")}
        rules=list(db.execute("SELECT id,premises FROM inference_rules WHERE kind='causal' ORDER BY id LIMIT 500"))
    by_key={f[:2]:f for f in facts}
    candidates={}
    for rule in rules:
        for p in json.loads(rule["premises"]):
            p=triple(p)
            original=by_key.get(p[:2])
            if original and original!=p:
                candidates.setdefault(p,{"replaced_fact":facts[original],"rule_ids":[]})["rule_ids"].append(rule["id"])
    worlds=[]
    for p,evidence in sorted(candidates.items())[:12]:
        result=simulate([p],path)
        result["evidence"]=evidence
        worlds.append((json.dumps(p,ensure_ascii=False),json.dumps(result,ensure_ascii=False),now()))
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("DELETE FROM imagined_worlds")
        db.executemany("INSERT INTO imagined_worlds VALUES (?,?,?)",worlds)
    return len(worlds)

def recent(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        return [json.loads(r[0]) for r in db.execute("SELECT result FROM imagined_worlds ORDER BY assumption LIMIT 5")]
