"""Optional Russian morphological analysis with conservative exact fallback."""
from functools import lru_cache
import re

@lru_cache(maxsize=1)
def analyzer():
    try:
        import pymorphy3
        return pymorphy3.MorphAnalyzer()
    except ImportError:
        return None

@lru_cache(maxsize=4096)
def lemma(word):
    engine=analyzer()
    if engine is None or not re.fullmatch(r"[а-яё]+",word):
        return word
    parses=engine.parse(word)
    if not parses:
        return word
    # Do not collapse ambiguous analyses into a single asserted meaning.
    forms={p.normal_form for p in parses if p.score>=parses[0].score*0.5}
    return next(iter(forms)) if len(forms)==1 else word

def signature(text):
    return tuple(lemma(w) for w in re.findall(r"\w+",text.casefold()))

def matches(term,query):
    a,b=signature(term),signature(query)
    return bool(a) and any(b[i:i+len(a)]==a for i in range(len(b)-len(a)+1))
