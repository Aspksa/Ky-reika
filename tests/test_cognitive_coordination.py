import unittest
from core.integral_intelligence import coordinate

class CoordinationTests(unittest.TestCase):
    def test_epistemic_risk(self):
        plan=coordinate("Вопрос",{"epistemic_audit":{"records":[{"issues":["missing_provenance"]}],"guidance":["Verify source"]}})
        self.assertEqual(plan["depth"],"deep")
        self.assertIn("Verify source",plan["checks"])
        self.assertEqual(plan["external_actions"],"propose_only")
    def test_integrity(self):
        self.assertEqual(coordinate("Вопрос",{"cognitive_integrity":{"issues":["conflict"]}})["depth"],"deep")
    def test_direct(self):
        self.assertEqual(coordinate("Привет",{})["depth"],"direct")
