"""Conservative remediation of observed local failures, not model retraining."""
GUIDANCE={
    "causal":"Recheck each causal premise, chain depth and source. Treat local causal predictions as provisional.",
    "conceptual":"Recheck observed set inclusion and exceptions. Never infer universal taxonomy from sampled overlap."
}
METHODS={"causal":"causal","conceptual":"abstraction"}

def prescribe(report):
    weak=set(report.get("weaknesses",[]))
    count=report.get("cases_per_skill")
    if isinstance(count,int) and count>0:
        weak.update(k for k,v in report.get("fixed_benchmark",{}).items() if v<count)
    return [{"skill":k,"method":METHODS[k],"guidance":GUIDANCE[k]} for k in sorted(weak) if k in GUIDANCE]

def adapt(plan,report):
    result=dict(plan)
    selected={m["method"] for m in plan["methods"]}
    remedies=[r for r in prescribe(report) if r["method"] in selected]
    if remedies:
        result["depth"]="deep"
        result["guidance"]=plan["guidance"]+" "+" ".join(r["guidance"] for r in remedies)
    result["targeted_practice"]=remedies
    return result
