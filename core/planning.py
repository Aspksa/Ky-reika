"""Ordered task plans linked to approved intentions."""
from .database import DB_PATH, connect, now
from .intentions import setup as init

def setup(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS plan_steps (
            id INTEGER PRIMARY KEY, intention_id INTEGER NOT NULL REFERENCES intentions(id),
            position INTEGER NOT NULL, description TEXT NOT NULL,
            completed TEXT, UNIQUE(intention_id,position))""")

def create(intention_id,steps,path=DB_PATH):
    if not isinstance(steps,(list,tuple)) or not 1<=len(steps)<=50 or any(not isinstance(s,str) or not s.strip() or len(s)>2000 for s in steps):
        raise ValueError("Invalid steps")
    setup(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        row=db.execute("SELECT status FROM intentions WHERE id=?",(intention_id,)).fetchone()
        if not row or row["status"] not in ("pending","active"):
            raise ValueError("Invalid intention")
        db.executemany("INSERT INTO plan_steps(intention_id,position,description) VALUES (?,?,?)",
                       [(intention_id,i,s.strip()) for i,s in enumerate(steps,1)])

def complete(step_id,path=DB_PATH):
    setup(path)
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        row=db.execute("""SELECT s.*,i.status FROM plan_steps s JOIN intentions i
            ON i.id=s.intention_id WHERE s.id=?""",(step_id,)).fetchone()
        if not row or row["status"]!="active" or row["completed"]:
            raise ValueError("Step unavailable")
        if db.execute("SELECT 1 FROM plan_steps WHERE intention_id=? AND position<? AND completed IS NULL",
                      (row["intention_id"],row["position"])).fetchone():
            raise ValueError("Previous steps incomplete")
        db.execute("UPDATE plan_steps SET completed=? WHERE id=?",(now(),step_id))

def active(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        return [dict(r) for r in db.execute("""SELECT s.*,i.description AS goal FROM plan_steps s
            JOIN intentions i ON i.id=s.intention_id WHERE i.status='active' AND s.completed IS NULL
            AND NOT EXISTS (SELECT 1 FROM plan_steps p WHERE p.intention_id=s.intention_id
            AND p.position<s.position AND p.completed IS NULL)
            ORDER BY i.priority DESC,s.id LIMIT 10""")]

def progress(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        rows=db.execute("""SELECT i.id,i.description,i.priority,i.due,i.status,
            count(s.id) AS total,count(s.completed) AS done
            FROM intentions i LEFT JOIN plan_steps s ON s.intention_id=i.id
            WHERE i.status IN ('active','pending')
            GROUP BY i.id ORDER BY i.priority DESC,i.id LIMIT 100""")
        result=[]
        for row in rows:
            item=dict(row)
            item["percent"]=round(100*item["done"]/item["total"]) if item["total"] else None
            item["overdue"]=bool(item["due"] and item["due"]<now() and item["status"]=="active")
            item["ready_to_finish"]=bool(item["status"]=="active" and item["total"] and item["done"]==item["total"])
            result.append(item)
        return result
