"""Generate bounded suggestions from existing cognitive state."""
from .database import DB_PATH, connect, initialize, now
from .planning import active
from .reflection import inspect

def setup(path=DB_PATH):
    initialize(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS initiatives (
            id INTEGER PRIMARY KEY, fingerprint TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending'
            CHECK(status IN ('pending','accepted','dismissed')), created TEXT NOT NULL)""")

def generate(path=DB_PATH):
    setup(path)
    report=inspect(path)
    candidates=[]
    if report["potential_conflicts"]:
        candidates.append(("conflicts","Review conflicting knowledge with the user."))
    if report["pending_knowledge"]:
        candidates.append(("knowledge","Review unconfirmed knowledge."))
    for step in active(path):
        candidates.append(("step:"+str(step["id"]),"Discuss next approved plan step: "+step["description"]))
    with connect(path) as db:
        db.executemany("INSERT OR IGNORE INTO initiatives(fingerprint,description,created) VALUES (?,?,?)",
                       [(key,description,now()) for key,description in candidates])
    return pending(path)

def pending(path=DB_PATH):
    setup(path)
    with connect(path) as db:
        return [dict(r) for r in db.execute("SELECT * FROM initiatives WHERE status='pending' ORDER BY id DESC LIMIT 10")]

def resolve(initiative_id,accept,path=DB_PATH):
    if not isinstance(accept,bool):
        raise ValueError("Explicit boolean required")
    setup(path)
    with connect(path) as db:
        cur=db.execute("UPDATE initiatives SET status=? WHERE id=? AND status='pending'",
                       ("accepted" if accept else "dismissed",initiative_id))
        if cur.rowcount!=1:
            raise ValueError("Unknown pending initiative")
