import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from core.sleep import consolidate
from core.reasoning import prepare
from core.database import connect

class BackgroundCycleTests(unittest.TestCase):
    def test_fresh_database_and_repeated_cycles(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"cycle.sqlite3"
            with patch.dict(os.environ,{"CLOUD_BACKGROUND_THINKING":"0","CLOUD_EMBED_MODEL":""}):
                for _ in range(2):
                    consolidate(path)
                    with connect(path) as db:
                        rows=list(db.execute("SELECT stage,status FROM maintenance_status"))
                        self.assertEqual(len(rows),28)
                        self.assertEqual([(r["stage"],r["status"]) for r in rows if r["status"]!="ok"],[])
                        self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0],"ok")
                        self.assertEqual(list(db.execute("PRAGMA foreign_key_check")),[])
                context=prepare("Проверка памяти и логики",path)
                self.assertIn("cognitive_integrity",context)
                self.assertIn("cognitive_health",context)
