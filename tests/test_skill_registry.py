import unittest
import sqlite3
from core.skill_registry import catalog

class SkillRegistryTests(unittest.TestCase):
    def test_evidence_separate_from_operation(self):
        with sqlite3.connect(":memory:") as db:
            db.row_factory=sqlite3.Row
            items=catalog(db,set(),{"training":{"status":"ok"}})
            self.assertTrue(all(s["evidence"] is None for s in items))
            db.execute("CREATE TABLE intelligence_training(id INTEGER, report TEXT, created TEXT)")
            db.execute("INSERT INTO intelligence_training VALUES (1,?,?)",('{"passed":{"causal":18},"cases_per_skill":20}',"2026-01-01"))
            items=catalog(db,{"intelligence_training"},{})
            self.assertEqual(next(s for s in items if s["id"]=="causal")["evidence"]["passed"],18)
