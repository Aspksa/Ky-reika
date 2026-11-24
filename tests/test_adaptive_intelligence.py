import unittest
from core.learning_review import evaluate

class AdaptiveIntelligenceTests(unittest.TestCase):
    def test_sustained_improvement(self):
        rows=[{"mode":m,"rating":v} for m,v in (("direct",0),("structured",1)) for _ in range(40)]
        self.assertEqual(evaluate(rows)["preferred"],"structured")
    def test_recent_reversal(self):
        rows=[{"mode":"direct","rating":0} for _ in range(100)]
        rows += [{"mode":"structured","rating":v} for v in [1]*90+[-1]*10]
        result=evaluate(rows)
        self.assertIsNone(result["preferred"])
        self.assertTrue(result["drift_warning"])
    def test_insufficient_evidence(self):
        self.assertIsNone(evaluate([])["preferred"])
