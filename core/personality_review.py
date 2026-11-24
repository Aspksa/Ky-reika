"""Local heuristic review; flags are candidates, not verified contradictions."""
import re
import json
from .database import DB_PATH, connect, now
from .cognition import setup

def inspect(answer):
    normalized=" ".join(answer.casefold().split())
    flags=[]
    # Only explicit first-person claims at the beginning of the response.
    if re.match(r"^я (?:настоящий человек|настоящая женщина|биологический организм)(?:[.!?,]|$)",normalized):
        flags.append("physical_identity_claim")
    if re.match(r"^у меня нет (?:никакой |долговременной )?памяти(?:[.!?,]|$)",normalized):
        flags.append("memory_denial")
    return flags

def record(message_id,answer,path=DB_PATH):
    setup(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS personality_reviews (
            message_id INTEGER PRIMARY KEY REFERENCES messages(id),
            flags TEXT NOT NULL, created TEXT NOT NULL)""")
        db.execute("INSERT OR IGNORE INTO personality_reviews VALUES (?,?,?)",
                   (message_id,json.dumps(inspect(answer)),now()))

def report(path=DB_PATH):
    from collections import Counter
    setup(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS personality_reviews (
            message_id INTEGER PRIMARY KEY REFERENCES messages(id),
            flags TEXT NOT NULL, created TEXT NOT NULL)""")
        rows=db.execute("SELECT message_id,flags FROM personality_reviews ORDER BY message_id DESC LIMIT 100").fetchall()
    counts=Counter(flag for row in rows for flag in json.loads(row["flags"]))
    return {"reviewed":len(rows),"signals":dict(counts),
            "review_candidates":[flag for flag,count in counts.items() if count>=3],
            "limitation":"Narrow textual heuristics; absence of flags does not establish consistency.",
            "trait_change_authorized":False}
