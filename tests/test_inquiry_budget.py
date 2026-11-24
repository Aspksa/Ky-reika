import unittest
from core.deep_inquiry import depth_budget

class InquiryBudgetTests(unittest.TestCase):
    def test_budget(self):
        self.assertEqual(depth_budget({},.5),4)
        self.assertEqual(depth_budget({},.9),6)
        self.assertEqual(depth_budget({"premises":[1]*20,"counterexamples":[1]*20},.9),12)
