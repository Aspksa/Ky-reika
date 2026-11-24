"""Background inquiry tree driven by evidence, not subjective consciousness."""
import json
from .database import DB_PATH, connect, now
from .development import setup as init

def setup(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS thought_nodes (
            id INTEGER PRIMARY KEY, root TEXT NOT NULL REFERENCES development_thoughts(fingerprint),
            parent INTEGER REFERENCES thought_nodes(id), stage INTEGER NOT NULL,
            revision INTEGER NOT NULL, content TEXT NOT NULL, created TEXT NOT NULL,
            UNIQUE(root,revision,stage))""")

def expand(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        roots=list(db.execute("""SELECT * FROM development_thoughts d WHERE status='candidate'
            AND NOT EXISTS (SELECT 1 FROM thought_nodes n WHERE n.root=d.fingerprint
            AND n.revision=d.observations AND n.stage=2) ORDER BY updated DESC LIMIT 20"""))
        for root in roots:
            key,rev=root["fingerprint"],root["observations"]
            previous=db.execute("SELECT id,stage FROM thought_nodes WHERE root=? AND revision=? ORDER BY stage DESC LIMIT 1",(key,rev)).fetchone()
            stage=previous["stage"]+1 if previous else 0
            hypothesis=json.loads(root["content"])
            prompts=[
                {"role":"inquirer","question":"What evidence would distinguish this hypothesis from alternatives?","hypothesis":hypothesis},
                {"role":"critic","question":"Which counterexamples or missing observations weaken it?","counterexamples":hypothesis.get("counterexamples",[]),"missing_conditions":hypothesis.get("possible_conditions",[])},
                {"role":"reviewer","status":"awaiting_evidence","question":"What new confirmed observations justify revisiting this conclusion?"}]
            db.execute("INSERT OR IGNORE INTO thought_nodes(root,parent,stage,revision,content,created) VALUES (?,?,?,?,?,?)",
                (key,previous["id"] if previous else None,stage,rev,json.dumps(prompts[stage],ensure_ascii=False),now()))
    return len(roots)

def recent(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        return [{"id":r["id"],"parent":r["parent"],"stage":r["stage"],"thought":json.loads(r["content"])}
                for r in db.execute("""SELECT n.* FROM thought_nodes n JOIN development_thoughts d ON d.fingerprint=n.root
                WHERE d.status='candidate' AND n.revision=d.observations ORDER BY n.id DESC LIMIT 10""")]
