import tempfile
import unittest
from pathlib import Path
from core.knowledge import propose, confirm
from core.inference import add_rule
from core.revision import revise, history

class BeliefRevisionTests(unittest.TestCase):
    def test_restoration(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"belief.sqlite3"
            def set_state(value):
                confirm(propose("device","state",value,"test",path=path),path)
            set_state("on")
            conclusion=("lamp","state","lit")
            add_rule([("device","state","on")],conclusion,path=path)
            self.assertEqual(revise(path)["added"],1)
            set_state("off")
            self.assertEqual(revise(path)["withdrawn"],1)
            set_state("on")
            self.assertEqual(revise(path)["restored"],1)
            versions=history(conclusion,path)
            self.assertEqual(len(versions),2)
            self.assertIsNotNone(versions[0]["withdrawn"])
            self.assertIsNone(versions[1]["withdrawn"])
