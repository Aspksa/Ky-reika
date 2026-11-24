"""Feedback-based strategy adaptation; observational scores are not causal effects."""
from .database import DB_PATH, connect
from .learning import setup as init

def setup(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS strategy_usage (
            message_id INTEGER PRIMARY KEY REFERENCES messages(id), mode TEXT NOT NULL,
            task TEXT NOT NULL)""")

def task_type(message):
    from .reasoning import tokens
    words=tokens(message)
    for task,keys in (("planning",{"план","plan","этапы"}),("comparison",{"сравни","compare"}),("diagnosis",{"ошибка","fix","error"})):
        if words & keys:
            return task
    return "general"

def record(message_id,message,strategy,path=DB_PATH):
    setup(path)
    mode=strategy["mode"]
    if mode not in ("direct","structured"):
        raise ValueError("Unknown strategy")
    with connect(path) as db:
        db.execute("INSERT OR IGNORE INTO strategy_usage VALUES (?,?,?)",(message_id,mode,task_type(message)))

def profile(message,path=DB_PATH):
    setup(path)
    with connect(path) as db:
        rows=[dict(r) for r in db.execute("""SELECT u.mode,count(*) AS samples,
            avg(f.rating) AS mean_rating FROM strategy_usage u JOIN response_feedback f
            ON f.message_id=u.message_id WHERE u.task=? GROUP BY u.mode""",(task_type(message),))]
    eligible=sorted((r for r in rows if r["samples"]>=5),key=lambda r:r["mean_rating"],reverse=True)
    preferred=eligible[0]["mode"] if len(eligible)==2 and eligible[0]["mean_rating"]-eligible[1]["mean_rating"]>=.3 else None
    return {"task":task_type(message),"observations":rows,"preferred":preferred}

def adapt(strategy,message,path=DB_PATH):
    report=profile(message,path)
    result=dict(strategy)
    from .learning_review import evaluate
    with connect(path) as db:
        rows=[dict(r) for r in db.execute("""SELECT u.mode,f.rating FROM strategy_usage u
            JOIN response_feedback f ON f.message_id=u.message_id WHERE u.task=?
            ORDER BY f.created,u.message_id""",(task_type(message),))]
    validation=evaluate(rows)
    result["learning_validation"]=validation
    if validation["preferred"]=="structured" and strategy["mode"]=="direct":
        result["mode"]="structured"
        result["guidance"]=list(dict.fromkeys(strategy.get("guidance",[])+["Organize the response into clear reasoning and verification steps."]))
    result["feedback_profile"]=report
    return result
