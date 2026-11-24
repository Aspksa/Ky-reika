import tempfile
import unittest
from pathlib import Path
from core.cognition import setup
from core.database import connect
from core.personality_statistics import profile

class PersonalityStatisticsTests(unittest.TestCase):
    def test_profile(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"test.sqlite3"
            setup(path)
            with connect(path) as db:
                tables={r[0] for r in db.execute("SELECT name FROM sqlite_master")}
                p=profile(db,tables)
                self.assertEqual(len(p["traits"]),10)
                self.assertEqual(len(p["affect"]),4)
                self.assertTrue(p["approval_required"])
                self.assertEqual(p["proposals"],[])
