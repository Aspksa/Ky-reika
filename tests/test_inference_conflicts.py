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

    def test_derived_conflict_quarantines_transitive_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"test.sqlite3"
            key=knowledge.propose("device","signal","yes","test",.9,path)
            knowledge.confirm(key,path)
            for a,b in [
                (("device","signal","yes"),("device","state","on")),
                (("device","state","on"),("device","output","light")),
                (("device","output","light"),("device","indicator","active")),
                (("device","signal","yes"),("device","state","off")),
                (("device","signal","yes"),("device","independent","yes")),
            ]:
                inference.add_rule([a],b,path=path)
            results={r["conclusion"]:r for r in inference.derive(path)}
            for predicate,value in [("state","on"),("state","off"),("output","light"),("indicator","active")]:
                self.assertTrue(results[("device",predicate,value)]["conflicts_with_confirmed"])
            self.assertFalse(results[("device","independent","yes")]["conflicts_with_confirmed"])
