import unittest
from core.integral_intelligence import coordinate

class TargetedPracticeTests(unittest.TestCase):
    def test_weak_conceptual_skill(self):
        context={"concepts":[{}],"intelligence_training":{"weaknesses":["conceptual"]}}
        self.assertEqual(coordinate("Понятие",context)["depth"],"deep")
        context["intelligence_training"]={"weaknesses":[]}
        self.assertEqual(coordinate("Понятие",context)["depth"],"focused")
    def test_unrelated_weakness(self):
        self.assertEqual(coordinate("Привет",{"intelligence_training":{"weaknesses":["causal"]}})["depth"],"direct")
