"""Observational feedback analysis, not independent correctness verification."""
from .database import DB_PATH, connect
from .learning import setup
from collections import Counter
import re

def summarize(rows):
    groups={}
    repeated=Counter()
    for row in rows:
        key=(row["task"],row["mode"])
        group=groups.setdefault(key,{"task":key[0],"mode":key[1],"samples":0,"negative":0,"rating_sum":0})
        group["samples"]+=1
        group["negative"]+=int(row["rating"]<0)
        group["rating_sum"]+=row["rating"]
        if row["rating"]<0:
            lesson=" ".join(row["lesson"].casefold().split())
            if lesson:
                repeated[lesson]+=1
    for group in groups.values():
        group["mean_rating"]=group.pop("rating_sum")/group["samples"]
    return {"strategies":list(groups.values()),
            "repeated_lessons":[{"lesson":lesson,"count":count} for lesson,count in repeated.most_common(10) if count>=2],
            "limitation":"Explicit feedback is observational; repeated comments are not verified errors.",
            "automatic_trait_change":False}

def report(path=DB_PATH):
    from .adaptation import setup as setup_strategy
    setup_strategy(path)
    with connect(path) as db:
        rows=[dict(r) for r in db.execute("""SELECT f.rating,f.lesson,
            coalesce(u.task,'unknown') AS task,coalesce(u.mode,'unknown') AS mode
            FROM response_feedback f LEFT JOIN strategy_usage u ON u.message_id=f.message_id
            ORDER BY f.created DESC,f.message_id DESC LIMIT 200""")]
    return summarize(rows)
