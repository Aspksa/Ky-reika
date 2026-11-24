import unittest
from core.inquiry_learning import summarize, prefer

class InquiryLearningTests(unittest.TestCase):
    def test_preference(self):
        rows=[{"mode":"audit","repetition_detected":True}]*10
        rows += [{"mode":"alternative","repetition_detected":False}]*10
        self.assertEqual(prefer("audit",summarize(rows)),"alternative")
        self.assertEqual(prefer("audit",summarize(rows[:11])),"audit")
        self.assertEqual(prefer("decompose",summarize(rows)),"decompose")
