"""Offline cognitive subsystem. All persistent state lives in the existing SQLite."""
import json
import math
from datetime import datetime, timezone
from .database import DB_PATH, TRAITS, connect, initialize, now

CONSTITUTION = {
    "identity": "Kyūreika, fictional Queen of Nine Tails",
    "constraints": ["Distinguish facts from hypotheses", "Respect user autonomy", "No autonomous external actions"],
    "self_facts": ["Software persona without a physical body"],
    "initiative": "propose_only",
    "baseline": dict(TRAITS),
}
LEVELS = ("working", "short", "episodic", "semantic", "archive")

def unit(value):
    value = float(value)
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Expected finite value between zero and one")
    return value

def setup(path=DB_PATH):
    initialize(path)
    with connect(path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS cognition_memory (
          id INTEGER PRIMARY KEY REFERENCES memories(id), level TEXT NOT NULL DEFAULT 'short',
          salience REAL NOT NULL, confidence REAL NOT NULL, usage_count INTEGER DEFAULT 0,
          contradiction_score REAL DEFAULT 0, decay_rate REAL DEFAULT 0.01,
          reward REAL DEFAULT 0, touched TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS cognition_affect (
          name TEXT PRIMARY KEY, value REAL NOT NULL, updated TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS cognition_observation (
          id INTEGER PRIMARY KEY, trait TEXT NOT NULL, target INTEGER NOT NULL,
          confidence REAL NOT NULL, source TEXT NOT NULL, UNIQUE(trait,source));
        CREATE TABLE IF NOT EXISTS cognition_proposal (
          id INTEGER PRIMARY KEY, trait TEXT NOT NULL, before INTEGER NOT NULL,
          after INTEGER NOT NULL, evidence TEXT NOT NULL, status TEXT DEFAULT 'pending');
        CREATE TABLE IF NOT EXISTS cognition_audit (
          id INTEGER PRIMARY KEY, event TEXT NOT NULL, payload TEXT NOT NULL, created TEXT NOT NULL);
        INSERT OR IGNORE INTO schema_version VALUES (2);
        """)
        db.execute("INSERT OR IGNORE INTO cognition_memory(id,salience,confidence,touched) SELECT id,importance/100.0,0.5,created_at FROM memories")
        for name, value in {"calm":.7,"affection":.7,"curiosity":.5,"irritation":.1}.items():
            db.execute("INSERT OR IGNORE INTO cognition_affect VALUES (?,?,?)",(name,value,now()))

def audit(db,event,payload):
    db.execute("INSERT INTO cognition_audit(event,payload,created) VALUES (?,?,?)",(event,json.dumps(payload,ensure_ascii=False),now()))

def experience(content, salience=.5, confidence=.5, path=DB_PATH):
    salience, confidence = unit(salience), unit(confidence)
    if not content.strip():
        raise ValueError("Empty memory")
    setup(path)
    with connect(path) as db:
        i=db.execute("INSERT INTO memories(content,importance,created_at) VALUES (?,?,?)",(content,round(salience*100),now())).lastrowid
        db.execute("INSERT INTO cognition_memory(id,salience,confidence,touched) VALUES (?,?,?,?)",(i,salience,confidence,now()))
        return i

def recall(query, limit=10, path=DB_PATH):
    setup(path)
    terms=set(query.casefold().split())
    with connect(path) as db:
        rows=[dict(r) for r in db.execute("SELECT m.content,c.* FROM memories m JOIN cognition_memory c ON m.id=c.id WHERE c.level!='archive'")]
        rows.sort(key=lambda r:(len(terms & set(r["content"].casefold().split())),r["salience"]*r["confidence"]),reverse=True)
        result=rows[:max(0,min(100,int(limit)))]
        db.executemany("UPDATE cognition_memory SET usage_count=usage_count+1 WHERE id=?",[(r["id"],) for r in result])
        return result

def affect(signals, path=DB_PATH):
    setup(path)
    with connect(path) as db:
        result={}
        for row in db.execute("SELECT * FROM cognition_affect").fetchall():
            name=row["name"]
            baseline={"calm":.7,"affection":.7,"curiosity":.5,"irritation":.1}[name]
            hours=max(0,(datetime.now(timezone.utc)-datetime.fromisoformat(row["updated"])).total_seconds()/3600)
            value=baseline+(row["value"]-baseline)*math.exp(-hours/6)
            if name in signals:
                value=.8*value+.2*unit(signals[name])
            db.execute("UPDATE cognition_affect SET value=?,updated=? WHERE name=?",(value,now(),name))
            result[name]=value
        return result

def observe(trait,target,confidence,source,path=DB_PATH):
    if trait not in TRAITS or not isinstance(target,int) or not 0<=target<=100 or not source.strip():
        raise ValueError("Invalid observation")
    confidence=unit(confidence)
    setup(path)
    with connect(path) as db:
        db.execute("INSERT OR IGNORE INTO cognition_observation(trait,target,confidence,source) VALUES (?,?,?,?)",(trait,target,confidence,source))

def reflect(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        proposals=[]
        for trait in TRAITS:
            before=db.execute("SELECT score FROM personality WHERE trait=?",(trait,)).fetchone()[0]
            rows=[dict(r) for r in db.execute("SELECT * FROM cognition_observation WHERE trait=? AND confidence>=.8",(trait,))]
            for direction in (-1,1):
                evidence=[r for r in rows if direction*(r["target"]-before)>=10]
                if len(evidence)<5 or len(evidence)<=len(rows)/2:
                    continue
                if db.execute("SELECT 1 FROM cognition_proposal WHERE trait=? AND status='pending'",(trait,)).fetchone():
                    continue
                after=max(0,min(100,before+direction*2))
                payload={"observations":evidence,"thresholds":{"drift":10,"confidence":.8,"count":5}}
                i=db.execute("INSERT INTO cognition_proposal(trait,before,after,evidence) VALUES (?,?,?,?)",(trait,before,after,json.dumps(payload))).lastrowid
                audit(db,"proposal",{"id":i,**payload})
                proposals.append(i)
        return proposals

def approve(proposal_id,path=DB_PATH):
    setup(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        p=db.execute("SELECT * FROM cognition_proposal WHERE id=? AND status='pending'",(proposal_id,)).fetchone()
        if not p:
            raise ValueError("No pending proposal")
        cur=db.execute("UPDATE personality SET score=? WHERE trait=? AND score=?",(p["after"],p["trait"],p["before"]))
        if cur.rowcount!=1:
            raise ValueError("Stale proposal")
        db.execute("UPDATE cognition_proposal SET status='applied' WHERE id=?",(proposal_id,))
        for item in json.loads(p["evidence"])["observations"]:
            db.execute("DELETE FROM cognition_observation WHERE id=?",(item["id"],))
        audit(db,"approved",dict(p))

def rollback(proposal_id,path=DB_PATH):
    setup(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        p=db.execute("SELECT * FROM cognition_proposal WHERE id=? AND status='applied'",(proposal_id,)).fetchone()
        if not p:
            raise ValueError("No applied proposal")
        if db.execute("SELECT 1 FROM cognition_proposal WHERE trait=? AND id>? AND status='applied'",(p["trait"],proposal_id)).fetchone():
            raise ValueError("Rollback newer changes first")
        cur=db.execute("UPDATE personality SET score=? WHERE trait=? AND score=?",(p["before"],p["trait"],p["after"]))
        if cur.rowcount!=1:
            raise ValueError("State changed")
        db.execute("UPDATE cognition_proposal SET status='rolled_back' WHERE id=?",(proposal_id,))
        audit(db,"rollback",dict(p))

def sleep_once(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        rows=db.execute("SELECT * FROM cognition_memory WHERE level!='archive'").fetchall()
        for r in rows:
            days=max(0,(datetime.now(timezone.utc)-datetime.fromisoformat(r["touched"])).total_seconds()/86400)
            score=r["salience"]*math.exp(-days*r["decay_rate"])
            level=r["level"]
            if score<.1 and days>=30:
                level="archive"
            elif level in ("working","short") and days>=1:
                level="episodic"
            if level!=r["level"]:
                audit(db,"memory_transition",{"id":r["id"],"from":r["level"],"to":level})
            db.execute("UPDATE cognition_memory SET salience=?,level=?,touched=? WHERE id=?",(score,level,now()))
    affect({},path)
    return reflect(path)
