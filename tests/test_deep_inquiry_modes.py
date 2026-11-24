import unittest
from core.deep_inquiry import choose_mode

class InquiryModesTests(unittest.TestCase):
    def test_progression(self):
        previous=[]
        for mode in ("decompose","alternative","audit","synthesis"):
            self.assertEqual(choose_mode(previous),mode)
            previous.append({"mode":mode,"decision":"audit"})
        self.assertEqual(choose_mode(previous),"audit")
