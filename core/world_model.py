"""Evidence-layered local world model; never promotes hypotheses to facts."""
import json
from .database import DB_PATH,connect,now
from .knowledge import setup
from .discovery_lab import recent
from .theoretical_intelligence import compare

def assemble(facts,predictions,conflicts):
    known={(f["subject"],f["predicate"]):f for f in facts}
    entities={}
    for f in facts:
        entities.setdefault(f["subject"],[]).append({"predicate":f["predicate"],"value":f["value"],"source_id":f["id"]})
    unknown=[]
    tensions=[]
    for p in predictions:
        s,k,v=p["candidate"]
        if p["status"]=="awaiting_evidence" and (s,k) not in known:
            unknown.append(p)
        elif p["status"]=="observed_counterexample":
            tensions.append(p)
    return {"entities":entities,"unknowns":unknown,"counterexamples":tensions,
            "pending_conflicts":conflicts,"theories":compare(predictions),
            "scope":"local confirmed records and selected provisional predictions",
            "factual_promotion_authorized":False}

def current(path=DB_PATH,predictions=None):
    setup(path)
    with connect(path) as db:
        facts=[dict(r) for r in db.execute("SELECT id,subject,predicate,value FROM knowledge_versions WHERE status='current' ORDER BY id DESC LIMIT 2000")]
        conflicts=[dict(r) for r in db.execute("""SELECT p.id AS pending_id,c.id AS current_id,p.subject,p.predicate
            FROM knowledge_versions p JOIN knowledge_versions c USING(subject,predicate)
            WHERE p.status='pending' AND c.status='current' AND p.value!=c.value LIMIT 50""")]
    return assemble(facts,recent(path) if predictions is None else predictions,conflicts)

def refresh(path=DB_PATH):
    model=current(path)
    content=json.dumps(model,ensure_ascii=False,sort_keys=True)
    with connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS world_model_versions (id INTEGER PRIMARY KEY, content TEXT NOT NULL, created TEXT NOT NULL)")
        old=db.execute("SELECT content FROM world_model_versions ORDER BY id DESC LIMIT 1").fetchone()
        if not old or old["content"]!=content:
            db.execute("INSERT INTO world_model_versions(content,created) VALUES (?,?)",(content,now()))
        db.execute("DELETE FROM world_model_versions WHERE id NOT IN (SELECT id FROM world_model_versions ORDER BY id DESC LIMIT 100)")
    return model

def relevant(message,path=DB_PATH,predictions=None):
    from .reasoning import tokens
    model=current(path,predictions)
    terms=tokens(message)
    model["entities"]={s:rows[:20] for s,rows in list((s,r) for s,r in model["entities"].items() if terms & tokens(s) or any(terms & tokens(x["predicate"]+" "+x["value"]) for x in r))[:10]}
    for key in ("unknowns","counterexamples"):
        model[key]=[p for p in model[key] if terms & tokens(" ".join(p["candidate"]))][:5]
    model["pending_conflicts"]=[c for c in model["pending_conflicts"] if terms & tokens(c["subject"]+" "+c["predicate"])][:5]
    return model
