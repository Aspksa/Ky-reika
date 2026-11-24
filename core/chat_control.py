"""Explicit local chat commands; never execute arbitrary model-generated code."""
import re
from .database import initialize, connect, now, DB_PATH

def command(message):
    normalized=" ".join(re.findall(r"\w+",message.casefold().replace("ё","е")))
    normalized=re.sub(r"^(проверь|выведи|покажи) ", "", normalized)
    normalized=re.sub(r"^(статус|состаяние|состоние|статистика) ", "состояние ", normalized)
    return {
        "состояние ядра":"status","покажи состояние ядра":"status",
        "диагностика":"status","диагностика ядра":"status",
        "состояние памяти":"memory","покажи состояние памяти":"memory",
        "состояние обучения":"learning","состояние исследований":"research",
        "состояние личности":"personality","состояние задач":"jobs",
        "команды ядра":"help","изучение языка":"language",
        "состояние языка":"language",
        "запусти обучение":"run_learning","обнови исследования":"run_research",
        "оптимизируй память":"run_memory",
    }.get(normalized)

def commands(message):
    parts=re.split(r"\s*(?:;|\n|,|\s+и\s+)\s*",message.strip())
    names=[command(part) for part in parts if part.strip()]
    return list(dict.fromkeys(names)) if names and all(names) else []

def execute(message,path=DB_PATH):
    from .semantic_memory import parse, record
    definition=parse(message)
    if definition:
        initialize(path)
        term,meaning=definition
        answer=f"Запомнила пользовательское значение «{term}»: {meaning}"
        with connect(path) as db:
            record(db,term,meaning,message)
            db.execute("INSERT INTO messages(role,content,created_at) VALUES ('user',?,?)",(message,now()))
            response_id=db.execute("INSERT INTO messages(role,content,created_at) VALUES ('assistant',?,?)",(answer,now())).lastrowid
        return answer,response_id
    names=commands(message)
    if not names:
        return None
    initialize(path)
    from .control_panel import report
    state=report(path)
    answer="\n\n".join(render(name,state,path) for name in names)
    with connect(path) as db:
        db.execute("INSERT INTO messages(role,content,created_at) VALUES ('user',?,?)",(message,now()))
        response_id=db.execute("INSERT INTO messages(role,content,created_at) VALUES ('assistant',?,?)",(answer,now())).lastrowid
    return answer,response_id

def render(name,state,path):
    if name.startswith("run_"):
        from .chat_tasks import enqueue
        task_id=enqueue(path,name[4:])
        return f"Поручение №{task_id} поставлено в очередь. Выполнение ещё не подтверждено."
    if name=="language":
        from .language_learning import candidates
        items=candidates(path)
        return "Кандидаты для изучения языка (частота сообщений, не доказательство незнания):\n"+("\n".join(f"{r['term']}: {r['occurrences']}" for r in items) or "Пока нет повторяющихся кандидатов.")
    if name=="help":
        answer="Команды: состояние ядра, состояние памяти, состояние обучения, состояние исследований, состояние личности, состояние задач; запусти обучение; обнови исследования; оптимизируй память."
    elif name=="status":
        stages=state["stages"]
        answer="Состояние ядра:\n"+("\n".join(f"{r['stage']}: {r['status']} (ошибок: {r['failures']})" for r in stages) if stages else "Фоновый цикл ещё не зарегистрирован.")
    elif name=="jobs":
        from .chat_tasks import recent
        answer="Очередь задач: "+str(state["jobs"])+"\nПоручения: "+str(recent(path))
    else:
        with connect(path) as db:
            tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            targets={"memory":("memories","messages"),"learning":("response_feedback","learning_reviews"),"research":("research_goals","background_reviews"),"personality":("personality","self_model_versions")}[name]
            answer="Состояние подсистемы:\n"+"\n".join(f"{table}: "+(str(db.execute("SELECT count(*) FROM "+table).fetchone()[0]) if table in tables else "ещё не создана") for table in targets)
    return answer
