import unittest
from core.structural_reasoning import closure,evaluate

class StructuralTests(unittest.TestCase):
    def test_conjunction(self):
        rules=[(("a","b"),"c"),(("c",),"a")]
        self.assertEqual(closure({"a"},rules),{"a"})
        self.assertEqual(closure({"a","b"},rules),{"a","b","c"})
    def test_empty_and_duplicate(self):
        self.assertEqual(closure(set(),[((),"a"),(("a","a"),"b")]),{"a","b"})
    def test_generated(self):
        self.assertEqual(evaluate(42)["passed"],40)
