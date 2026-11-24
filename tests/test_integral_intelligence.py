import unittest
from core.integral_intelligence import coordinate

class IntegralTests(unittest.TestCase):
    def test_direct(self):
        self.assertEqual(coordinate("Привет",{})["depth"],"direct")
    def test_conflict(self):
        self.assertEqual(coordinate("Вопрос",{"potential_conflicts":[{}]})["depth"],"deep")
    def test_multiple_methods(self):
        result=coordinate("Почему? Сравни",{"concepts":[{}]})
        self.assertEqual(result["depth"],"deep")
        self.assertEqual({m["method"] for m in result["methods"]},{"causal","abstraction","strategic"})
        self.assertEqual(result["external_actions"],"propose_only")
