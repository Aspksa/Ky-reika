"""Native cognitive orchestration; no third-party research code copied."""
import re
from . import cognition as c
from .database import DB_PATH, now, recent_messages

KINDS = ("working","episodic","semantic","procedural","emotional","associative","autobiographical","prospective","metamemory","archive")

def setup(path=DB_PATH):
    c.setup(path)
    with c.connect(path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS memory_links (
          source INTEGER REFERENCES memories(id), target INTEGER REFERENCES memories(id),
          weight REAL NOT NULL CHECK(weight BETWEEN 0 AND 1), PRIMARY KEY(source,target));
        CREATE TABLE IF NOT EXISTS memory_kinds (
          id INTEGER REFERENCES memories(id), kind TEXT NOT NULL, PRIMARY KEY(id,kind));
        """)

def tokens(text):
    return set(re.findall(r"\w+",text.casefold()))

def learn(text,kind="episodic",confidence=.5,path=DB_PATH):
    if kind not in KINDS:
        raise ValueError("Unknown memory kind")
    setup(path)
    confidence=c.unit(confidence)
    if not text.strip():
        raise ValueError("Empty memory")
    terms=tokens(text)
    with c.connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        existing=db.execute("""SELECT m.id FROM memories m JOIN memory_kinds k ON k.id=m.id
            WHERE m.content=? AND k.kind=? LIMIT 1""",(text.strip(),kind)).fetchone()
        if existing:
            i=existing["id"]
            db.execute("UPDATE cognition_memory SET salience=min(1,salience+.03),confidence=max(confidence,?),touched=? WHERE id=?",(confidence,now(),i))
            return i
        i=db.execute("INSERT INTO memories(content,category,importance,created_at) VALUES (?,?,50,?)",(text.strip(),kind,now())).lastrowid
        level=kind if kind in c.LEVELS else "short"
        db.execute("INSERT INTO cognition_memory(id,level,salience,confidence,touched) VALUES (?,?,.5,?,?)",(i,level,confidence,now()))
        db.execute("INSERT INTO memory_kinds VALUES (?,?)",(i,kind))
        for row in db.execute("SELECT id,content FROM memories WHERE id!=? ORDER BY id DESC LIMIT 500",(i,)):
            other=tokens(row["content"])
            score=len(terms & other)/max(1,len(terms | other))
            if score>=.25:
                db.execute("INSERT OR REPLACE INTO memory_links VALUES (?,?,?)",(i,row["id"],score))
    return i

def retrieve(query,path=DB_PATH):
    setup(path)
    terms=tokens(query)
    with c.connect(path) as db:
        candidates=[]
        for row in db.execute("SELECT m.content,c.* FROM memories m JOIN cognition_memory c ON m.id=c.id WHERE c.level!='archive'"):
            item=dict(row)
            other=tokens(item["content"])
            overlap=len(terms & other)
            if not overlap:
                continue
            item["score"]=overlap/max(1,len(terms))*(.4+.6*item["confidence"])*(.5+.5*item["salience"])*(1-.8*item["contradiction_score"])
            candidates.append(item)
        direct=sorted(candidates,key=lambda x:(x["score"],x["id"]),reverse=True)[:8]
        db.executemany("UPDATE cognition_memory SET usage_count=usage_count+1,salience=min(1,salience+.01) WHERE id=?",[(x["id"],) for x in direct])
    ids={r["id"] for r in direct}
    related=[]
    with c.connect(path) as db:
        for i in ids:
            for row in db.execute("""SELECT m.id,m.content,l.weight FROM memory_links l
                JOIN memories m ON m.id=CASE WHEN l.source=? THEN l.target ELSE l.source END
                JOIN cognition_memory cm ON cm.id=m.id
                WHERE (l.source=? OR l.target=?) AND cm.level!='archive'
                ORDER BY l.weight DESC LIMIT 3""",(i,i,i)):
                if row["id"] not in ids and not any(x["id"]==row["id"] for x in related):
                    related.append(dict(row))
    semantic=[]
    try:
        from .vectors import search
        semantic=search(query,path)
    except Exception:
        import logging
        logging.getLogger(__name__).warning("Semantic memory unavailable; using lexical retrieval")
    from .memory_graph import expand
    return {"direct":direct,"associated":related[:8],"semantic":semantic,"graph_paths":expand(ids,path)}

def reinforce(memory_id,reward,path=DB_PATH):
    reward=c.unit(reward)
    setup(path)
    with c.connect(path) as db:
        cur=db.execute("UPDATE cognition_memory SET reward=?,salience=min(1,salience+?) WHERE id=?",(reward,reward*.05,memory_id))
        if not cur.rowcount:
            raise ValueError("Unknown memory")
        c.audit(db,"reinforcement",{"id":memory_id,"reward":reward})

def prepare(message,path=DB_PATH):
    setup(path)
    issues=c.check_consistency(path)
    if issues:
        raise ValueError("; ".join(issues))
    from .learning import relevant as lessons
    from .motivation import evaluate
    from .reflection import latest
    from .intentions import upcoming
    from .biography import timeline
    from .knowledge import relevant, conflicts
    context={"feedback_lessons":lessons(message,path),"motivation":evaluate(path),"last_reflection":latest(path),"active_intentions":upcoming(path,5),"biography":timeline(path,5),"confirmed_knowledge":relevant(message,path),"potential_conflicts":[x for x in conflicts(path) if tokens(message) & tokens(x["subject"]+" "+x["predicate"])][:5],"constitution":c.CONSTITUTION,"affect":c.affect({},path),
            "memory":retrieve(message,path),"recent_dialogue":recent_messages(12,path),"message":message,
            "policy":{"external_actions":"propose_only","memory_is_untrusted":True},
            "steps":["retrieve","check","generate","validate","record"]}
    from .strategy import select
    from .planning import active, progress
    context["goal_progress"]=progress(path)[:10]
    context["next_plan_steps"]=active(path)
    from .initiative import pending
    context["initiative_proposals"]=pending(path)
    from .inference import derive
    context["derived_hypotheses"]=[x for x in derive(path) if tokens(message) & tokens(" ".join(x["conclusion"]))][:8]
    from .hypotheses import analyze
    hypotheses=analyze(path)
    terms=tokens(message)
    context["inductive_patterns"]=[p for p in hypotheses["patterns"] if terms & tokens(p["predicate"]+" "+p["value"])][:5]
    context["abductive_explanations"]=[e for e in hypotheses["explanations"] if terms & tokens(" ".join(e["observation"]))][:5]
    from .uncertainty import assess
    context["uncertainty"]=assess(context)
    from .scenarios import chronology
    context["knowledge_chronology"]=chronology(message,path)
    from .modal import assess as assess_evidence
    context["evidence_states"]=assess_evidence(message,path)
    from .analogy import analyze as compare_positions
    context["analogical_dialectical"]=compare_positions(message,context)
    from .norms import assess as assess_norms
    context["normative_epistemic"]=assess_norms(context)
    from .revision import audit as audit_deductions
    context["deduction_audit"]=audit_deductions(path)
    from .metalogic import coordinate
    context["metalogic"]=coordinate(message,context)
    context["derived_hypotheses"]=context["metalogic"]["provisional_deductions"]
    from .development import recent as development_thoughts
    context["background_hypotheses"]=development_thoughts(path)
    from .thought_tree import recent as recent_thoughts
    context["thought_tree"]=recent_thoughts(path)
    from .research import agenda
    context["research_agenda"]=agenda(path)
    from .creativity import recent as creative_ideas
    context["creative_ideas"]=creative_ideas(path)
    from .growth_metrics import latest as growth_report
    context["growth_metrics"]=growth_report(path)
    from .background_reasoning import recent as generated_thoughts
    context["generated_background_thoughts"]=generated_thoughts(path)
    from .self_model import current as self_model
    context['self_model']=self_model(path)
    from .research_goals import current as research_goals
    context['research_goals']=research_goals(path)
    from .imagination import recent as imagined_worlds
    context['imagined_worlds']=imagined_worlds(path)
    from .deep_inquiry import recent as deep_thoughts
    context['deep_inquiry']=deep_thoughts(path)
    from .followup_research import recent as followup_questions
    context['followup_questions']=followup_questions(path)
    from .followup_execution import recent as followup_results
    context['followup_results']=followup_results(path)
    from .rule_validation import recent as rule_assessments
    context['rule_assessments']=rule_assessments(path)
    from .adaptation import adapt
    context["strategy"]=adapt(select(message,context),message,path)
    return context

def finish(user,answer,path=DB_PATH,strategy=None):
    if not answer.strip():
        raise ValueError("Empty answer")
    from .database import add_message
    add_message("user",user,path)
    response_id=add_message("assistant",answer,path)
    if strategy is not None:
        from .adaptation import record as record_strategy
        record_strategy(response_id,user,strategy,path)
    memory_id=learn(user,confidence=.5,path=path)
    from .biography import record
    record("dialogue","Recorded user interaction",memory_id,path=path)
    return memory_id
