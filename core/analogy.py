"""Analogical candidates and dialectical comparison, not proof by similarity."""
from .database import DB_PATH

def compare(left,right):
    from .reasoning import tokens
    a,b=tokens(left),tokens(right)
    return {"similarity":len(a&b)/max(1,len(a|b)),
            "shared_terms":sorted(a&b),"left_only":sorted(a-b),"right_only":sorted(b-a)}

def analyze(message,context):
    candidates=[]
    memory=context.get("memory",{})
    for item in memory.get("direct",[])+memory.get("associated",[]):
        comparison=compare(message,item["content"])
        if comparison["similarity"]>=.15:
            candidates.append({"memory_id":item["id"],**comparison,
                "status":"analogy_candidate"})
    candidates.sort(key=lambda x:x["similarity"],reverse=True)
    debates=[]
    for conflict in context.get("potential_conflicts",[]):
        debates.append({"subject":conflict["subject"],"predicate":conflict["predicate"],
            "thesis":{"value":conflict["current_value"],"source":conflict["current_source"]},
            "antithesis":{"value":conflict["proposed_value"],"source":conflict["proposed_source"]},
            "comparison":compare(conflict["current_value"],conflict["proposed_value"]),
            "resolution":"unresolved; verify evidence and distinguish contexts before proposing synthesis"})
    return {"analogies":candidates[:5],"opposing_positions":debates[:5],
            "guidance":"Lexical similarity is not structural equivalence. Do not infer truth or force a compromise."}
