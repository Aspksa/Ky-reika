"""Follow-up inquiry with persistent stages and explicit evidence boundaries."""
import json
import os
from .database import DB_PATH, connect, now
from .research import setup as init

def setup(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS deep_inquiry (
            root TEXT NOT NULL, revision INTEGER NOT NULL, round INTEGER NOT NULL,
            status TEXT NOT NULL, content TEXT, created TEXT NOT NULL,
            PRIMARY KEY(root,revision,round))""")

def advance(path=DB_PATH,request=None):
    if os.environ.get("CLOUD_BACKGROUND_THINKING","1")!="1":
        return False
    model=os.environ.get("CLOUD_MODEL","")
    if not model or (request is None and not (os.environ.get("CLOUD_API_KEY") and os.environ.get("CLOUD_API_BASE","").startswith("https://"))):
        return False
    setup(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='background_reviews' AND type='table'").fetchone():
            return False
        row=db.execute("""SELECT b.root,b.revision,b.content,a.question,d.content AS candidate,
            (SELECT count(*) FROM deep_inquiry i WHERE i.root=b.root AND i.revision=b.revision) AS rounds
            FROM background_reviews b JOIN research_agenda a ON a.root=b.root AND a.revision=b.revision
            JOIN development_thoughts d ON d.fingerprint=b.root AND d.observations=b.revision
            WHERE b.status='unverified' AND d.status='candidate'
            AND NOT EXISTS (SELECT 1 FROM deep_inquiry i WHERE i.root=b.root AND i.revision=b.revision AND i.status='reserved')
            AND (SELECT count(*) FROM deep_inquiry i WHERE i.root=b.root AND i.revision=b.revision)<3
            ORDER BY rounds,a.priority DESC,b.root LIMIT 1""").fetchone()
        if not row:
            return False
        root,revision,number=row["root"],row["revision"],row["rounds"]+1
        previous=[json.loads(r[0]) for r in db.execute("""SELECT content FROM deep_inquiry
            WHERE root=? AND revision=? AND status='unverified' ORDER BY round""",(root,revision))]
        db.execute("INSERT INTO deep_inquiry VALUES (?,?,?,'reserved',NULL,?)",(root,revision,number,now()))
    if request is None:
        from .gateway import request
    from .background_reasoning import stage
    instructions=[
        "Audit the candidate's logical premises. Separate evidence identifiers from unsupported claims. Identify a counterexample.",
        "Develop competing explanations. Compare their assumptions and identify what evidence would distinguish them.",
        "Synthesize the inquiry. Identify unresolved gaps and formulate a concrete next research question. Do not promote any claim to fact."
    ]
    try:
        result=stage(request,model,row["question"],{"candidate":json.loads(row["candidate"]),
            "initial_review":json.loads(row["content"]),"previous_rounds":previous},instructions[number-1])
        content=json.dumps(result,ensure_ascii=False)
        status="unverified"
    except Exception:
        content=None
        status="failed"
    with connect(path) as db:
        db.execute("UPDATE deep_inquiry SET status=?,content=? WHERE root=? AND revision=? AND round=?",(status,content,root,revision,number))
    return status=="unverified"

def recent(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        return [{"root":r["root"],"round":r["round"],"status":"unverified",**json.loads(r["content"])}
            for r in db.execute("""SELECT i.* FROM deep_inquiry i JOIN development_thoughts d
            ON d.fingerprint=i.root AND d.observations=i.revision
            WHERE d.status='candidate' AND i.status='unverified' ORDER BY i.created DESC LIMIT 5""")]
