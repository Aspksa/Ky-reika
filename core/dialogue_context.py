"""Bounded role-preserving conversation context for follow-up requests."""
import re
from .database import recent_messages

FOLLOWUPS={"делай","продолжай","дальше","сливай","реализуй","объедини","это","всё","все","continue","proceed"}

def is_followup(message):
    words=set(re.findall(r"\w+",message.casefold()))
    return len(words)<=12 and bool(words & FOLLOWUPS)

def history(path,message):
    rows=recent_messages(40 if is_followup(message) else 16,path)
    selected=[]
    remaining=24000
    for row in reversed(rows):
        if row["role"] not in ("user","assistant"):
            continue
        content=row["content"]
        if remaining<=0:
            break
        if len(content)>remaining:
            content="[Начало сообщения опущено]\n"+content[-remaining:]
        selected.append({"role":row["role"],"content":content})
        remaining-=len(content)
    return list(reversed(selected))

def messages(system,message,context):
    return [{"role":"system","content":system},
            *context.get("conversation_history",[]),
            {"role":"user","content":message}]
