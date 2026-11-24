"""Repeatable local skill checks; not an IQ measurement."""
import random
from .causal_analysis import trace
from .concept_relations import discover

def evaluate(seed=42,count=20):
    rng=random.Random(seed)
    scores={"causal":0,"conceptual":0}
    for i in range(count):
        n=rng.randint(2,6)
        nodes=[("object","stage"+str(j),"yes") for j in range(n+1)]
        rules=[(j+1,[nodes[j]],nodes[j+1]) for j in range(n)]
        rng.shuffle(rules)
        result=trace([(nodes[0],1)],rules)
        final=next((r for r in result if r["conclusion"]==nodes[-1]),{})
        scores["causal"]+=int(final.get("depth")==n and final.get("sources")==[1] and final.get("status")=="conditional_prediction")
        rows=[]
        for j in range(n+3):
            rows.append({"id":len(rows)+1,"subject":str(j),"predicate":"a","value":"yes"})
            if j<3:
                rows.append({"id":len(rows)+1,"subject":str(j),"predicate":"b","value":"yes"})
        rng.shuffle(rows)
        relations=discover(rows)
        scores["conceptual"]+=int(any(r["left"]==["b","yes"] and r["right"]==["a","yes"] and r["relation"]=="observed_subset" for r in relations))
    return {"seed":seed,"cases_per_skill":count,"passed":scores,
            "weaknesses":[k for k,v in scores.items() if v<count],
            "limitation":"Synthetic local regression checks, not general intelligence or cloud model evaluation."}

if __name__=="__main__":
    import json
    print(json.dumps(evaluate(),indent=2))
