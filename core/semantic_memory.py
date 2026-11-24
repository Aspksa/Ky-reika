"""User-defined vocabulary, separate from verified factual knowledge."""
import re
import unicodedata
from .database import connect, now, DB_PATH

def normalize(text):
    return " ".join(unicodedata.normalize("NFC",text).casefold().split())

def setup(db):
    db.execute("""CREATE TABLE IF NOT EXISTS semantic_definitions (
        id INTEGER PRIMARY KEY, term TEXT NOT NULL, meaning TEXT NOT NULL,
        source TEXT NOT NULL, created TEXT NOT NULL)""")
    db.execute("CREATE INDEX IF NOT EXISTS semantic_term ON semantic_definitions(term,id)")

def parse(message):
    match=re.fullmatch(r'\s*(?:запомни значение|уточни значение)\s+["«]([^"»\n]+)["»]\s*[:=]\s*(.+)',message,re.I|re.S)
    if not match:
        return None
    term,meaning=normalize(match[1]),match[2].strip()
    if not term or not meaning or len(term)>120 or len(meaning)>2000:
        return None
    return term,meaning

def record(db,term,meaning,source):
    setup(db)
    db.execute("INSERT INTO semantic_definitions(term,meaning,source,created) VALUES (?,?,?,?)",(term,meaning,source,now()))

def relevant(message,path=DB_PATH):
    query=normalize(message)
    with connect(path) as db:
        setup(db)
        rows=db.execute("""SELECT d.term,d.meaning,d.id FROM semantic_definitions d
            WHERE d.id=(SELECT max(id) FROM semantic_definitions WHERE term=d.term)
            ORDER BY d.id DESC""")
        result=[]
        for row in rows:
            if re.search(r"(?<!\w)"+re.escape(row["term"])+r"(?!\w)",query):
                result.append({**dict(row),"authority":"user_defined_context_only"})
                if len(result)>=20:
                    break
        return result
