"""Software motivational profile; interests are inferred signals, not feelings."""
from collections import Counter
from .database import DB_PATH, connect
from . import cognition, intellectual_goals, intentions
import re

TOPICS={
    "logic":{"логика","логики","рассуждение","доказательство","logic"},
    "memory":{"память","памяти","воспоминания","memory"},
    "personality":{"личность","личности","характер","характера","personality"},
    "research":{"исследование","исследования","гипотеза","research"},
    "software":{"код","программа","программы","github","python"},
}
def interests(messages):
    counts=Counter()
    for message in messages:
        words=set(re.findall(r"\w+",message.casefold()))
        for topic,terms in TOPICS.items():
            if words & terms:
                counts[topic]+=1
    return [{"topic":topic,"observations":count} for topic,count in sorted(counts.items(),key=lambda x:(-x[1],x[0])) if count>=3]

def profile(path=DB_PATH):
    cognition.setup(path)
    with connect(path) as db:
        messages=[r[0] for r in db.execute("SELECT content FROM messages WHERE role='user' ORDER BY id DESC LIMIT 200")]
    goals=intellectual_goals.current(path)
    return {"interests":interests(messages),"sample_size":len(messages),
            "research_goals":[{"root":g["root"],"question":g["question"],"priority":g["priority"],"status":g["status"]} for g in goals],
            "approved_intentions":intentions.upcoming(path,5),
            "authority":"internal_research_and_proposals_only",
            "limitation":"Topic frequency reflects dialogue exposure, not subjective desire."}
