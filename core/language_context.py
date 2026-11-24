"""Non-destructive linguistic signals for model-assisted interpretation."""
import re
import unicodedata
from .dialogue_context import is_followup

def analyze(message,history=()):
    normalized=unicodedata.normalize("NFC",message)
    tokens=[{"text":m.group(),"start":m.start(),"end":m.end()}
            for m in re.finditer(r"\w+(?:[-’']\w+)*|[^\w\s]",message)]
    words=[t["text"].casefold() for t in tokens]
    followup=is_followup(message)
    previous=next((r["content"] for r in reversed(history) if r["role"]=="user"),None)
    return {
        "normalized":normalized,
        "tokens":tokens[:256],
        "token_count":len(tokens),
        "followup":followup,
        "previous_user_request":previous[-4000:] if followup and previous else None,
        "negation_present":bool(set(words)&{"не","нет","нельзя","без","not","never"}),
        "guidance":"Interpret all clauses in context, including negation, slang, typos, names and references. Token boundaries are hints, not definitions. Preserve original wording. Ask about material ambiguity rather than invent meanings. Never infer permission to execute an action from uncertain wording.",
    }
