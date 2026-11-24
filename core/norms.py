"""Explicit norms and evidence status; never grant execution authority."""
def normative(action,rules):
    if not isinstance(action,str) or not action.strip():
        raise ValueError("Invalid action")
    matched=[r for r in rules if r["action"]==action]
    kinds={r["kind"] for r in matched}
    if not kinds <= {"permission","prohibition","obligation"}:
        raise ValueError("Invalid norm")
    conflict="prohibition" in kinds and bool(kinds & {"permission","obligation"})
    return {"action":action,"norms":sorted(kinds),"conflict":conflict,
            "status":"forbidden" if "prohibition" in kinds else "required" if "obligation" in kinds else "permitted" if "permission" in kinds else "unspecified",
            "execution_authorized":False}

def epistemic(context):
    disputed={x["current_id"] for x in context.get("potential_conflicts",[])}
    facts=[{"id":f["id"],"status":"disputed" if f["id"] in disputed else "confirmed_record",
            "confidence":f["confidence"]} for f in context.get("confirmed_knowledge",[])]
    return {"facts":facts,"derived_status":"inferred_not_confirmed",
            "pattern_status":"hypothesis","missing_evidence":"unknown_not_false",
            "guidance":"Confirmed records can still be wrong. Distinguish evidence, inference and speculation."}

def assess(context):
    return {"epistemic":epistemic(context),
            "normative":normative("execute_external_action",[{"action":"execute_external_action","kind":"prohibition"}]),
            "proposal":normative("propose_external_action",[{"action":"propose_external_action","kind":"permission"}])}
