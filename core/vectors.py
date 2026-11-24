"""Optional semantic retrieval using an OpenAI-compatible embeddings endpoint."""
import json
import math
import os
from .database import DB_PATH, connect
from .cognition import setup as init

def setup(path=DB_PATH):
    init(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS memory_vectors (
            memory_id INTEGER REFERENCES memories(id) ON DELETE CASCADE,
            namespace TEXT NOT NULL, vector TEXT NOT NULL,
            PRIMARY KEY(memory_id,namespace))""")

def embed(text,model):
    from .gateway import request
    data=request("/embeddings",{"model":model,"input":text})
    v=[float(x) for x in data["data"][0]["embedding"]]
    norm=math.sqrt(sum(x*x for x in v))
    if not v or not math.isfinite(norm) or norm<=0 or len(v)>16384:
        raise ValueError("Invalid embedding")
    return [x/norm for x in v]

def search(query,path=DB_PATH):
    model=os.environ.get("CLOUD_EMBED_MODEL","").strip()
    if not model:
        return []
    namespace=os.environ.get("CLOUD_API_BASE","").rstrip("/")+"|"+model
    setup(path)
    q=embed(query,model)
    with connect(path) as db:
        missing=db.execute("""SELECT m.id,m.content FROM memories m
            JOIN cognition_memory c ON c.id=m.id
            LEFT JOIN memory_vectors v ON v.memory_id=m.id AND v.namespace=?
            WHERE v.memory_id IS NULL AND c.level!='archive'
            ORDER BY m.id DESC LIMIT 4""",(namespace,)).fetchall()
    for row in missing:
        v=embed(row["content"],model)
        with connect(path) as db:
            db.execute("INSERT OR REPLACE INTO memory_vectors VALUES (?,?,?)",(row["id"],namespace,json.dumps(v)))
    with connect(path) as db:
        rows=db.execute("""SELECT m.id,m.content,c.confidence,c.salience,c.contradiction_score,v.vector
            FROM memory_vectors v JOIN memories m ON m.id=v.memory_id
            JOIN cognition_memory c ON c.id=m.id
            WHERE v.namespace=? AND c.level!='archive'""",(namespace,)).fetchall()
    result=[]
    for row in rows:
        item=dict(row)
        v=json.loads(item.pop("vector"))
        if len(v)!=len(q):
            continue
        similarity=sum(a*b for a,b in zip(q,v))
        if similarity>=.45:
            item["similarity"]=similarity
            item["score"]=similarity*(.5+.5*item["confidence"])*(1-.8*item["contradiction_score"])
            result.append(item)
    return sorted(result,key=lambda r:r["score"],reverse=True)[:6]
