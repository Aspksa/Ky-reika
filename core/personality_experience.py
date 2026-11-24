"""Adapt communication preferences, never core identity or trait scores."""
from .database import DB_PATH, connect
from .learning import setup

PREFERENCES={
    "length":{"отвечай короче":"concise","отвечай подробнее":"detailed"},
    "tone":{"общайся теплее":"warm","общайся нейтральнее":"neutral"},
}
def evaluate(rows):
    result={}
    for dimension,phrases in PREFERENCES.items():
        votes=[(phrases[" ".join(r["lesson"].casefold().strip(" .!").split())],r["message_id"])
               for r in rows if " ".join(r["lesson"].casefold().strip(" .!").split()) in phrases]
        recent=votes[:5]
        if len(recent)>=3 and len({v[0] for v in recent[:3]})==1:
            result[dimension]={"preference":recent[0][0],"evidence_ids":[v[1] for v in recent[:3]]}
    return {"preferences":result,"core_traits_unchanged":True,
            "guidance":"Apply preferences only when compatible with the current explicit request and constitution."}

def profile(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        rows=[dict(r) for r in db.execute("SELECT message_id,lesson FROM response_feedback WHERE lesson!='' ORDER BY created DESC,message_id DESC LIMIT 200")]
    return evaluate(rows)
