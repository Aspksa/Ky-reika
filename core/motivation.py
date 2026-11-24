"""Deterministic priorities derived from recorded state."""
from .database import DB_PATH, connect
from . import cognition, intentions, reflection

def evaluate(path=DB_PATH):
    cognition.setup(path)
    report=reflection.inspect(path)
    goals=intentions.upcoming(path,10)
    with connect(path) as db:
        traits=dict(db.execute("SELECT trait,score FROM personality"))
    priorities=[
        {"kind":"verify_knowledge","score":min(1,(report["potential_conflicts"]+report["disputed_memories"])/5)},
        {"kind":"review_pending","score":min(1,report["pending_knowledge"]/10)},
        {"kind":"pursue_approved_goals","score":max((1 if g["due_now"] else g["priority"]/5 for g in goals),default=0)},
        {"kind":"clarify_uncertainty","score":min(1,report["low_confidence"]/20)}
    ]
    return {"traits":traits,"priorities":sorted(priorities,key=lambda p:p["score"],reverse=True),
            "initiative":"propose_only"}

def feedback(trait,target,source,confidence=.8,path=DB_PATH):
    """Record explicit feedback; changes require existing approval workflow."""
    cognition.observe(trait,target,confidence,source,path)
    return cognition.reflect(path)
