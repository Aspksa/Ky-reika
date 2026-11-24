"""Versioned selection for synthetic graph exercises only."""
import json
from .database import now

BASELINE={"indexed":False,"fifo":False}

def select(report,previous=None):
    candidates=report["candidates"]
    def valid(row):
        return all(row[k]["passed"]==24 for k in ("training","validation"))
    baseline=next(r for r in candidates if r["method"]==BASELINE)
    eligible=[r for r in candidates if valid(r) and all(r[k]["work"]<baseline[k]["work"] for k in ("training","validation"))]
    if not valid(baseline):
        return {"method":None,"status":"suspended"}
    if not eligible:
        return {"method":dict(BASELINE),"status":"baseline"}
    best=min(eligible,key=lambda r:(r["training"]["work"],r["validation"]["work"]))
    old=next((r for r in eligible if r["method"]==previous),None)
    if old and old["training"]["work"]<=best["training"]["work"]:
        best=old
    return {"method":best["method"],"status":"validated"}

def record(db,report):
    db.execute("""CREATE TABLE IF NOT EXISTS method_library (
        revision INTEGER PRIMARY KEY, selection TEXT NOT NULL, evidence TEXT NOT NULL, created TEXT NOT NULL)""")
    row=db.execute("SELECT revision,selection FROM method_library ORDER BY revision DESC LIMIT 1").fetchone()
    previous=json.loads(row["selection"]) if row else {}
    selection=select(report,previous.get("method"))
    if selection!=previous:
        revision=db.execute("INSERT INTO method_library(selection,evidence,created) VALUES (?,?,?)",
            (json.dumps(selection),json.dumps(report),now())).lastrowid
    else:
        revision=row["revision"]
    return {**selection,"revision":revision,"scope":"synthetic_graph_exercises"}

def gate_transfer(selection,transfer):
    """Do not authorize an experimental method without transfer validation."""
    result=dict(selection)
    if selection.get("status")=="validated" and (transfer.get("status")!="transfer_validated" or transfer.get("method")!=selection.get("method")):
        result.update(method=None,status="suspended",reason="transfer_not_validated")
    return result
