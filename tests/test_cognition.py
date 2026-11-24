import tempfile
import unittest
from pathlib import Path
from core import cognition as c

class CognitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "test.sqlite3"
        c.setup(self.path)

    def test_memory(self):
        i = c.experience("test memory", .9, .8, self.path)
        self.assertEqual(c.recall("test", path=self.path)[0]["id"], i)
        c.sleep_once(self.path)
        self.assertEqual(c.recall("test", path=self.path)[0]["usage_count"], 1)

    def test_affect(self):
        self.assertGreater(c.affect({"curiosity": 1}, self.path)["curiosity"], .5)
        with self.assertRaises(ValueError):
            c.affect({"curiosity": float("nan")}, self.path)

    def test_evolution_and_rollback(self):
        for i in range(4):
            c.observe("jealousy", 40, .9, str(i), self.path)
        self.assertEqual(c.reflect(self.path), [])
        c.observe("jealousy", 40, .9, "4", self.path)
        p, = c.reflect(self.path)
        self.assertEqual(c.reflect(self.path), [])
        c.approve(p, self.path)
        with c.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT score FROM personality WHERE trait='jealousy'").fetchone()[0], 63)
        c.rollback(p, self.path)
        with c.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT score FROM personality WHERE trait='jealousy'").fetchone()[0], 65)
