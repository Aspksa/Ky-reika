"""Pure routing heuristics; uncertain and compound requests use full reasoning."""
import re

SOCIAL={"привет","здравствуй","здравствуйте","доброе утро","добрый вечер",
        "спасибо","благодарю","hi","hello","thanks","кто ты","как тебя зовут",
        "кто я для тебя","как дела","как ты","доброй ночи"}
COMPLEX={"почему","докажи","сравни","проанализируй","обоснуй","рассчитай",
         "причина","последствия","стратегия","план","ошибка","противоречие",
         "why","prove","compare","analyze","calculate"}
REFERENCES={"это","этот","эта","такое","его","её","их","выше","предыдущий","дальше"}

def route(message,history=()):
    normalized=" ".join(message.casefold().split()).rstrip("!.?… ")
    if normalized in SOCIAL:
        return "social"
    words=set(re.findall(r"\w+",normalized))
    if len(normalized.split())>12 or words & COMPLEX or "\n" in message:
        return "deep"
    if re.fullmatch(r"(что такое|что означает|дай определение|как называется|what is|define) [\w -]+",normalized):
        subject=re.sub(r"^(что такое|что означает|дай определение|как называется|what is|define) ","",normalized)
        if set(subject.split()) & REFERENCES:
            return "deep"
        # A recent complex request may make a short definition a follow-up.
        previous=next((r.get("content","") for r in reversed(history) if r.get("role")=="user"),"")
        if set(re.findall(r"\w+",previous.casefold())) & COMPLEX:
            return "deep"
        return "standard"
    return "deep"
