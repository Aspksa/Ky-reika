import unittest
from core.cognitive_integrity import assess, apply

class IntegrityTests(unittest.TestCase):
    def test_inconsistent_identity(self):
        context={"self_model":{"autonomy":"propose_only"},
                 "policy":{"external_actions":"propose_only"},
                 "intellectual_identity":{"observed_rounds":1,"dominant_method":"audit","methods":{"audit":{"samples":1}}}}
        report=assess(context)
        self.assertIn("unsupported_dominant_method",report["issues"])
        self.assertEqual(apply({"mode":"direct"},report)["mode"],"structured")
        self.assertEqual(apply({},report)["external_actions"],"propose_only")
