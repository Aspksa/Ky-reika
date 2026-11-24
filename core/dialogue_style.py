"""Conservative dialogue adaptation from local history, without extra cloud calls."""
import re
from statistics import median
from .database import DB_PATH, recent_messages
from .cognition import affect

def profile(message,path=DB_PATH):
    rows=[r["content"] for r in recent_messages(60,path) if r["role"]=="user"]
    words=re.findall(r"\w+",message.casefold())
    signals={}
    if message.strip().casefold().rstrip("!.") in ("спасибо","благодарю","thanks"):
        signals={"affection":.9,"calm":.85}
    elif message.rstrip().endswith("?"):
        signals={"curiosity":.8}
    from .personality_experience import profile as experience_profile
    return {"experience_preferences":experience_profile(path),"samples":len(rows),"typical_words":median(len(r.split()) for r in rows) if rows else None,
            "current_words":len(words),"affect":affect(signals,path),
            "guidance":"Match explicit request first; historical message length is only a weak style signal. Affect is simulated, not a diagnosis or a fact about the user."}
