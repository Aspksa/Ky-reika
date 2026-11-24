import unittest
from core.metacognition import assess, apply

class MetacognitiveIntelligenceTests(unittest.TestCase):
    def test_cross_method_risks(self):
        report=assess({"confirmed_knowledge":[{"id":1}],
            "causal_chains":[{"status":"disputed"}],
            "creative_candidates":[{}],"concept_relations":[{}],
            "strategic_options":[{"risks":["deadline_passed"]}]})
        self.assertEqual(report["status"],"review_required")
        self.assertEqual(report["checks"]["disputed_causal_chains"],1)
        self.assertEqual(report["checks"]["strategic_risks"],1)
        self.assertEqual(len(report["guidance"]),3)
        strategy=apply({"mode":"direct","guidance":["Preserve constraints"],"external_actions":"propose_only"},report)
        self.assertEqual(strategy["mode"],"structured")
        self.assertIn("Preserve constraints",strategy["guidance"])
        self.assertEqual(strategy["external_actions"],"propose_only")
    def test_no_detected_issue(self):
        self.assertEqual(assess({"confirmed_knowledge":[{"id":1}]})["status"],"no_detected_issue")
