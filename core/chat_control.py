"""Explicit local chat commands; never execute arbitrary model-generated code."""
import re
from .database import initialize, connect, now, DB_PATH

def command(message):
    normalized=" ".join(re.findall(r"\w+",message.casefold().replace("ё","е")))
    return {
        "состояние ядра":"status","покажи состояние ядра":"status",
        "диагностика":"status","диагностика ядра":"status",
        "состояние памяти":"memory","покажи состояние памяти":"memory",
        "состояние обучения":"learning","состояние исследований":"research",
        "состояние личности":"personality","состояние задач":"jobs",
        "команды ядра":"help",
    }.get(normalized)

def execute(message,path=DB_PATH):
    name=command(message)
    if name is None:
        return None
    initialize(path)
    from .control_panel import report
    state=report(path)
    if name=="help":
        answer="Команды: состояние ядра, состояние памяти, состояние обучения, состояние исследований, состояние личности, состояние задач."
    elif name=="status":
        stages=state["stages"]
        answer="Состояние ядра:\n"+("\n".join(f"{r['stage']}: {r['status']} (ошибок: {r['failures']})" for r in stages) if stages else "Фоновый цикл ещё не зарегистрирован.")
    elif name=="jobs":
        answer="Очередь задач: "+str(state["jobs"])
    else:
        with connect(path) as db:
            tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            targets={"memory":("memories","messages"),"learning":("response_feedback","learning_reviews"),"research":("research_goals","background_reviews"),"personality":("personality","self_model_versions")}[name]
            answer="Состояние подсистемы:\n"+"\n".join(f"{table}: "+(str(db.execute("SELECT count(*) FROM "+table).fetchone()[0]) if table in tables else "ещё не создана") for table in targets)
    with connect(path) as db:
        db.execute("INSERT INTO messages(role,content,created_at) VALUES ('user',?,?)",(message,now()))
        response_id=db.execute("INSERT INTO messages(role,content,created_at) VALUES ('assistant',?,?)",(answer,now())).lastrowid
    return answer,response_id
