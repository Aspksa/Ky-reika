"""Native cognitive orchestration; no third-party research code copied."""
import re
from . import cognition as c
from .database import DB_PATH, now

KINDS = ("working","episodic","semantic","procedural","emotional","associative","autobiographical","prospective","metamemory","archive")

def setup(path=DB_PATH):
    c.setup(path)
    with c.connect(path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS memory_links (
          source INTEGER REFERENCES memories(id), target INTEGER REFERENCES memories(id),
          weight REAL NOT NULL CHECK(weight BETWEEN 0 AND 1), PRIMARY KEY(source,target));
        CREATE TABLE IF NOT EXISTS memory_kinds (
          id INTEGER REFERENCES memories(id), kind TEXT NOT NULL, PRIMARY KEY(id,kind));
        """)

def tokens(text):
    return set(re.findall(r"\w+",text.casefold()))

def learn(text,kind="episodic",confidence=.5,path=DB_PATH):
    if kind not in KINDS:
        raise ValueError("Unknown memory kind")
    setup(path)
    i=c.experience(text,confidence=confidence,path=path)
    terms=tokens(text)
    with c.connect(path) as db:
        db.execute("INSERT INTO memory_kinds VALUES (?,?)",(i,kind))
        for row in db.execute("SELECT id,content FROM memories WHERE id!=? ORDER BY id DESC LIMIT 500",(i,)):
            other=tokens(row["content"])
            score=len(terms & other)/max(1,len(terms | other))
            if score>=.25:
                db.execute("INSERT OR REPLACE INTO memory_links VALUES (?,?,?)",(i,row["id"],score))
    return i

def retrieve(query,path=DB_PATH):
    setup(path)
    direct=c.recall(query,limit=8,path=path)
    ids={r["id"] for r in direct}
    related=[]
    with c.connect(path) as db:
        for i in ids:
            for row in db.execute("""SELECT m.id,m.content,l.weight FROM memory_links l
                JOIN memories m ON m.id=CASE WHEN l.source=? THEN l.target ELSE l.source END
                JOIN cognition_memory cm ON cm.id=m.id
                WHERE (l.source=? OR l.target=?) AND cm.level!='archive'
                ORDER BY l.weight DESC LIMIT 3""",(i,i,i)):
                if row["id"] not in ids and not any(x["id"]==row["id"] for x in related):
                    related.append(dict(row))
    return {"direct":direct,"associated":related[:8]}

def reinforce(memory_id,reward,path=DB_PATH):
    reward=c.unit(reward)
    setup(path)
    with c.connect(path) as db:
        cur=db.execute("UPDATE cognition_memory SET reward=?,salience=min(1,salience+?) WHERE id=?",(reward,reward*.05,memory_id))
        if not cur.rowcount:
            raise ValueError("Unknown memory")
        c.audit(db,"reinforcement",{"id":memory_id,"reward":reward})

def prepare(message,path=DB_PATH):
    setup(path)
    issues=c.check_consistency(path)
    if issues:
        raise ValueError("; ".join(issues))
    return {"constitution":c.CONSTITUTION,"affect":c.affect({},path),
            "memory":retrieve(message,path),"message":message,
            "policy":{"external_actions":"propose_only","memory_is_untrusted":True},
            "steps":["retrieve","check","generate","validate","record"]}

def finish(user,answer,path=DB_PATH):
    if not answer.strip():
        raise ValueError("Empty answer")
    from .database import add_message
    add_message("user",user,path)
    add_message("assistant",answer,path)
    return learn(user,confidence=.5,path=path)
