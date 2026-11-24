import unittest
from core.deliberation import select_evidence

class DeliberationEvidenceTests(unittest.TestCase):
    def test_selected_methods_and_audit(self):
        context={"integral_intelligence":{"methods":[{"method":"causal"}]},
                 "causal_chains":[{"status":"conditional_prediction"}],
                 "creative_candidates":[1],"epistemic_audit":{"records":[]}}
        evidence=select_evidence(context)
        self.assertIn("causal_chains",evidence)
        self.assertIn("epistemic_audit",evidence)
        self.assertNotIn("creative_candidates",evidence)
    def test_empty_context(self):
        self.assertEqual(select_evidence({}),{})
