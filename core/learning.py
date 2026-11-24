"""Learning from explicit feedback, without changing model weights."""
from .database import DB_PATH, initialize, connect, now

def setup(path=DB_PATH):
    initialize(path)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS response_feedback (
            message_id INTEGER PRIMARY KEY REFERENCES messages(id),
            rating INTEGER NOT NULL CHECK(rating BETWEEN -1 AND 1),
            lesson TEXT NOT NULL, created TEXT NOT NULL)""")

def record(message_id,rating,lesson="",path=DB_PATH):
    if rating not in (-1,0,1) or not isinstance(lesson,str) or len(lesson)>2000:
        raise ValueError("Invalid feedback")
    setup(path)
    with connect(path) as db:
        row=db.execute("SELECT role FROM messages WHERE id=?",(message_id,)).fetchone()
        if not row or row["role"]!="assistant":
            raise ValueError("Unknown assistant response")
        db.execute("""INSERT INTO response_feedback VALUES (?,?,?,?)
            ON CONFLICT(message_id) DO UPDATE SET rating=excluded.rating,
            lesson=excluded.lesson,created=excluded.created""",(message_id,rating,lesson.strip(),now()))

def relevant(query,path=DB_PATH):
    from .reasoning import tokens
    setup(path)
    terms=tokens(query)
    with connect(path) as db:
        rows=[dict(r) for r in db.execute("""SELECT f.*,m.content FROM response_feedback f
            JOIN messages m ON m.id=f.message_id WHERE f.lesson!=''
            ORDER BY f.created DESC LIMIT 500""")]
    scored=[(len(terms & tokens(r["lesson"]+" "+r["content"])),r) for r in rows]
    return [{"lesson":r["lesson"],"rating":r["rating"],"message_id":r["message_id"]}
            for score,r in sorted(scored,key=lambda x:x[0],reverse=True)[:5] if score]
