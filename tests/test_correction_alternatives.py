import unittest
from core.correction_queue import alternatives

class CorrectionAlternativesTests(unittest.TestCase):
    def test_competing_values(self):
        result=alternatives({"id":1,"value":"on"},[{"id":2,"value":"off"},{"id":3,"value":"on"}])
        self.assertEqual(len(result["candidates"]),2)
        self.assertFalse(result["evidence_sufficient"])
        self.assertTrue(result["unknown_possible"])
        self.assertEqual(result["candidates"][1]["record_ids"],[1,3])
    def test_single_claim_not_proof(self):
        self.assertFalse(alternatives({"id":1,"value":"on"},[])["evidence_sufficient"])
