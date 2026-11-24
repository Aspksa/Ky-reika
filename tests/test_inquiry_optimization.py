import unittest
from core.deep_inquiry import choose_mode, similarity

class OptimizationTests(unittest.TestCase):
    def test_similarity(self):
        self.assertEqual(similarity("Check new evidence","new evidence check"),1)
        self.assertEqual(similarity("plant","device"),0)

    def test_switch(self):
        previous=[{"mode":m,"decision":"audit"} for m in
                  ("decompose","alternative","synthesis","audit","audit")]
        self.assertNotEqual(choose_mode(previous),"audit")
