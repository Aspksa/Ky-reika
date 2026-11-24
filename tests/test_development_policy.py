import unittest
from core.development_policy import choose

class DevelopmentPolicyTests(unittest.TestCase):
    def test_idle(self):
        self.assertEqual(choose(0,{})["interval"],3600)
    def test_backlog(self):
        self.assertEqual(choose(30,{"thought_steps":0})["thought_budget"],25)
        self.assertEqual(choose(30,{})["interval"],900)
    def test_bounds(self):
        for n in range(100):
            self.assertLessEqual(choose(n,{"thought_steps":0})["thought_budget"],30)
