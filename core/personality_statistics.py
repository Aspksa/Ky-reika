"""Read-only profile of stored software persona parameters."""
from .database import TRAITS
from .inner_motivation import interests

def profile(db,tables):
    scores=dict(db.execute("SELECT trait,score FROM personality")) if "personality" in tables else {}
    affect=[dict(r) for r in db.execute("SELECT name,value,updated FROM cognition_affect ORDER BY name")] if "cognition_affect" in tables else []
    proposals=[dict(r) for r in db.execute("SELECT id,trait,before,after,status FROM cognition_proposal ORDER BY id DESC LIMIT 20")] if "cognition_proposal" in tables else []
    messages=[r[0] for r in db.execute("SELECT content FROM messages WHERE role='user' ORDER BY id DESC LIMIT 200")] if "messages" in tables else []
    return {"traits":[{"name":k,"baseline":v,"value":scores.get(k)} for k,v in TRAITS.items()],
            "affect":affect,"proposals":proposals,"interests":interests(messages),"sample_size":len(messages),
            "approval_required":True}
