import tempfile
import unittest
from pathlib import Path
from core import knowledge, inference

class ConflictTests(unittest.TestCase):
    def test_conflicting_conclusion_cannot_be_premise(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"test.sqlite3"
            for predicate,value in [("state","off"),("signal","yes")]:
                key=knowledge.propose("device",predicate,value,"test",.9,path)
                knowledge.confirm(key,path)
            inference.add_rule([("device","signal","yes")],("device","state","on"),path=path)
            inference.add_rule([("device","state","on")],("device","output","light"),path=path)
            results=inference.derive(path)
            self.assertTrue(any(r["conflicts_with_confirmed"] for r in results))
            self.assertNotIn(("device","output","light"),[r["conclusion"] for r in results])
