"""Associative links preserve source memories; similarity is not factual agreement."""
from .database import DB_PATH, connect
from .reasoning import setup, tokens

def consolidate(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        rows=[(r["id"],tokens(r["content"])) for r in db.execute("""SELECT m.id,m.content FROM memories m
            JOIN cognition_memory c ON c.id=m.id WHERE c.level!='archive' ORDER BY m.id DESC LIMIT 300""")]
        count=0
        for i,(a,x) in enumerate(rows):
            for b,y in rows[i+1:]:
                score=len(x & y)/max(1,len(x | y))
                if score>=.35:
                    cur=db.execute("INSERT OR IGNORE INTO memory_links VALUES (?,?,?)",(a,b,score))
                    count+=cur.rowcount
        return count

def expand(seeds,path=DB_PATH):
    setup(path)
    seen=set(seeds)
    frontier=[(i,1.0,[i]) for i in sorted(seen)[:8]]
    results=[]
    with connect(path) as db:
        for depth in range(2):
            next_frontier=[]
            for node,weight,trail in frontier:
                for r in db.execute("""SELECT m.id,m.content,l.weight,c.confidence,c.contradiction_score
                    FROM memory_links l JOIN memories m ON m.id=CASE WHEN l.source=? THEN l.target ELSE l.source END
                    JOIN cognition_memory c ON c.id=m.id WHERE (l.source=? OR l.target=?) AND c.level!='archive'
                    ORDER BY l.weight DESC,m.id LIMIT 5""",(node,node,node)):
                    if r["id"] in seen:
                        continue
                    score=weight*r["weight"]*(1-.8*r["contradiction_score"])
                    if score<.12:
                        continue
                    seen.add(r["id"])
                    route=trail+[r["id"]]
                    results.append({"id":r["id"],"content":r["content"],"score":score,"source_path":route,"confidence":r["confidence"],"status":"association_not_fact"})
                    next_frontier.append((r["id"],score,route))
            frontier=sorted(next_frontier,key=lambda x:x[1],reverse=True)[:8]
    return sorted(results,key=lambda x:x["score"],reverse=True)[:8]
