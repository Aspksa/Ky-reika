"""Catalog of implemented capabilities and separately measured local checks."""
import json

SKILLS=(
    ("language","Языковой анализ","language_learning",None),
    ("memory","Ассоциативная память","graph",None),
    ("causal","Причинно-следственный анализ","training","causal"),
    ("conceptual","Связи между понятиями","training","conceptual"),
    ("logic","Проверка логических правил","rules",None),
    ("research","Исследования","research",None),
    ("creativity","Творческие идеи","creativity",None),
    ("imagination","Моделирование сценариев","imagination",None),
    ("learning","Обучение на обратной связи","learning",None),
    ("reflection","Самоанализ","reflection",None),
    ("identity","Модель личности","self",None),
    ("prediction","Проверка прогнозов","predictions",None),
    ("discovery","Формирование гипотез","discovery",None),
    ("health","Диагностика","health",None),
)

def catalog(db,tables,stages):
    training={}
    updated=None
    if "intelligence_training" in tables:
        row=db.execute("SELECT report,created FROM intelligence_training ORDER BY id DESC LIMIT 1").fetchone()
        if row:
            training=json.loads(row["report"])
            updated=row["created"]
    result=[]
    for key,label,stage,benchmark in SKILLS:
        passed=training.get("passed",{}).get(benchmark)
        total=training.get("cases_per_skill")
        evidence=None
        if benchmark and type(passed) is int and type(total) is int and 0<=passed<=total and total>0:
            evidence={"passed":passed,"total":total,"updated":updated,"kind":"synthetic_local"}
        result.append({"id":key,"label":label,"stage":stage,"operation":stages.get(stage,{}).get("status","unobserved"),"evidence":evidence})
    return result
