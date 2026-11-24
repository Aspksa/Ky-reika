"""Read-only strategic assessment of approved goals; no invented deadlines or execution."""
from .database import DB_PATH
from .planning import progress, active

def assess(goals,steps):
    next_steps={s["intention_id"]:s for s in steps}
    result=[]
    for goal in goals:
        if goal["status"]!="active":
            continue
        step=next_steps.get(goal["id"])
        risks=[]
        if goal["overdue"]:
            risks.append("deadline_passed")
        if not goal["total"]:
            risks.append("missing_plan")
        if goal["ready_to_finish"]:
            options=["verify_completion_against_goal","request_completion_confirmation"]
        elif not goal["total"]:
            options=["decompose_goal","clarify_constraints"]
        elif goal["overdue"]:
            options=["reassess_remaining_scope","propose_revised_deadline","continue_if_still_feasible"]
        else:
            options=["continue_next_step","check_dependencies_and_acceptance_criteria"]
        result.append({"goal_id":goal["id"],"goal":goal["description"],"priority":goal["priority"],
            "progress":goal["percent"],"due":goal["due"],"risks":risks,
            "next_step":step["description"] if step else None,"options":options,
            "status":"proposal_only","execution_authorized":False,
            "limitation":"No resource estimates or dependency verification inferred from progress alone."})
    return sorted(result,key=lambda r:(-int("deadline_passed" in r["risks"]),-r["priority"],r["goal_id"]))[:10]

def current(path=DB_PATH):
    return assess(progress(path),active(path))
