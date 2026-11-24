"""Probability and fuzzy membership are distinct quantities."""
import math

def unit(value):
    value=float(value)
    if not math.isfinite(value) or not 0<=value<=1:
        raise ValueError("Expected finite value in [0,1]")
    return value

def bayes(prior,likelihood,alternative_likelihood):
    p,a,b=map(unit,(prior,likelihood,alternative_likelihood))
    evidence=p*a+(1-p)*b
    if evidence==0:
        raise ValueError("Impossible evidence under supplied model")
    return p*a/evidence

def fuzzy_and(*values):
    return min(map(unit,values))

def fuzzy_or(*values):
    return max(map(unit,values))

def fuzzy_not(value):
    return 1-unit(value)

def membership(value,low,high):
    value,low,high=map(float,(value,low,high))
    if not all(map(math.isfinite,(value,low,high))) or low>=high:
        raise ValueError("Invalid membership interval")
    return max(0.,min(1.,(value-low)/(high-low)))

def assess(context):
    """Heuristic evidence quality, not a calibrated probability."""
    facts=context.get("confirmed_knowledge",[])
    confidence=[unit(f["confidence"]) for f in facts]
    conflicts=len(context.get("potential_conflicts",[]))
    quality=sum(confidence)/len(confidence) if confidence else None
    return {"evidence_quality":quality,"conflict_count":conflicts,
            "uncertainty_membership":None if quality is None else fuzzy_or(fuzzy_not(quality),membership(conflicts,0,3)),
            "guidance":"Scores are heuristics, not probabilities of truth. Do not invent likelihoods."}
