"""Compose candidate associations for investigation, not new confirmed facts."""
import json
from .database import DB_PATH, connect, now
from .development import setup as init

def setup(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS creative_ideas (
            left_root TEXT REFERENCES development_thoughts(fingerprint),
            right_root TEXT REFERENCES development_thoughts(fingerprint),
            content TEXT NOT NULL, updated TEXT NOT NULL,
            PRIMARY KEY(left_root,right_root))""")

def generate(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        rows=[(r["fingerprint"],json.loads(r["content"])) for r in db.execute(
            "SELECT * FROM development_thoughts WHERE kind='rule' AND status='candidate' ORDER BY fingerprint LIMIT 50")]
        db.execute("DELETE FROM creative_ideas")
        count=0
        for left,a in rows:
            for right,b in rows:
                if left==right or a["conclusion"]!=b["premise"] or a["premise"][0]==b["conclusion"][0]:
                    continue
                idea={"premise":a["premise"],"bridge":a["conclusion"],"candidate":b["conclusion"],
                      "status":"speculative_combination","question":"Does the proposed association survive direct testing?",
                      "guidance":"Association is not transitive; verify independently."}
                db.execute("INSERT INTO creative_ideas VALUES (?,?,?,?)",(left,right,json.dumps(idea,ensure_ascii=False),now()))
                count+=1
                if count>=20:
                    return count
        return count

def recent(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        return [{"sources":[r["left_root"],r["right_root"]],**json.loads(r["content"])}
                for r in db.execute("""SELECT i.* FROM creative_ideas i
                JOIN development_thoughts a ON a.fingerprint=i.left_root
                JOIN development_thoughts b ON b.fingerprint=i.right_root
                WHERE a.status='candidate' AND b.status='candidate'
                ORDER BY i.updated DESC LIMIT 5""")]
