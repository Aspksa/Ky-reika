import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from core import reasoning, knowledge, inference, revision, uncertainty, modal, scenarios

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"test.sqlite3"
        env=patch.dict(os.environ,{"CLOUD_EMBED_MODEL":""})
        env.start()
        self.addCleanup(env.stop)

    def fact(self,value):
        i=knowledge.propose("device","state",value,"test",.9,self.path)
        knowledge.confirm(i,self.path)

    def test_full_context_and_memory(self):
        self.fact("on")
        inference.add_rule([("device","state","on")],("device","output","light"),path=self.path)
        context=reasoning.prepare("device",self.path)
        self.assertIn("metalogic",context)
        self.assertTrue(context["derived_hypotheses"])
        reasoning.finish("device","Recorded",self.path)
        self.assertTrue(reasoning.prepare("device",self.path)["recent_dialogue"])

    def test_revision(self):
        self.fact("on")
        inference.add_rule([("device","state","on")],("device","output","light"),path=self.path)
        self.assertEqual(revision.revise(self.path)["active"],1)
        self.fact("off")
        self.assertTrue(revision.audit(self.path)["stale_records"])
        self.assertEqual(revision.revise(self.path)["withdrawn"],1)

    def test_logic(self):
        self.assertAlmostEqual(uncertainty.bayes(.5,.8,.2),.8)
        self.assertEqual(modal.evidence(True,True),"conflicting")
        self.fact("on")
        inference.add_rule([("device","state","on")],("device","output","light"),"causal",self.path)
        result=scenarios.simulate([("device","state","off")],self.path)
        self.assertIn(("device","output","light"),result["removed"])
        self.assertEqual(knowledge.relevant("device",self.path)[0]["value"],"on")
