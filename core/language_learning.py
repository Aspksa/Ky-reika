"""Incremental language exposure ledger; frequency is not semantic verification."""
import re
from .database import connect, DB_PATH
from .morphology import lemma

def refresh(path=DB_PATH):
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS language_cursor (id INTEGER PRIMARY KEY CHECK(id=1), last_id INTEGER NOT NULL)")
        db.execute("INSERT OR IGNORE INTO language_cursor VALUES (1,0)")
        db.execute("""CREATE TABLE IF NOT EXISTS language_exposure (
            term TEXT PRIMARY KEY, occurrences INTEGER NOT NULL,
            first_message INTEGER NOT NULL, last_message INTEGER NOT NULL)""")
        cursor=db.execute("SELECT last_id FROM language_cursor WHERE id=1").fetchone()[0]
        rows=db.execute("SELECT id,content FROM messages WHERE role='user' AND id>? ORDER BY id LIMIT 100",(cursor,)).fetchall()
        for row in rows:
            terms={lemma(w) for w in re.findall(r"[а-яё]{3,}|[a-z]{3,}",row["content"].casefold()) if len(w)<=80}
            for term in terms:
                db.execute("""INSERT INTO language_exposure VALUES (?,1,?,?)
                    ON CONFLICT(term) DO UPDATE SET occurrences=occurrences+1,last_message=excluded.last_message""",(term,row["id"],row["id"]))
            db.execute("UPDATE language_cursor SET last_id=? WHERE id=1",(row["id"],))
    return len(rows)

def candidates(path=DB_PATH,limit=20):
    with connect(path) as db:
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "language_exposure" not in tables:
            return []
        exclude=" AND NOT EXISTS (SELECT 1 FROM semantic_definitions d WHERE d.term=e.term)" if "semantic_definitions" in tables else ""
        return [{**dict(r),"status":"unverified_language_candidate"} for r in db.execute(
            "SELECT term,occurrences,first_message,last_message FROM language_exposure e WHERE occurrences>=2"+exclude+" ORDER BY occurrences DESC,last_message DESC,term LIMIT ?",(limit,))]
