import sqlite3
import unittest
from core.research_statistics import report

class ResearchStatisticsTests(unittest.TestCase):
    def test_empty_and_goals(self):
        with sqlite3.connect(":memory:") as db:
            db.row_factory=sqlite3.Row
            self.assertIsNone(report(db,set())["counts"]["goals"])
            db.execute("CREATE TABLE research_goals(root TEXT, revision INTEGER, question TEXT, priority REAL, status TEXT, updated TEXT)")
            db.execute("INSERT INTO research_goals VALUES ('a',1,'question',1,'queued','2026-01-01')")
            result=report(db,{"research_goals"})
            self.assertEqual(result["counts"]["goals"],1)
            self.assertEqual(result["goals"][0]["status"],"queued")
