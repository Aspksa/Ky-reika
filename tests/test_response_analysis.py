import unittest
from core.response_analysis import summarize

class ResponseAnalysisTests(unittest.TestCase):
    def test_repeated_negative_comments(self):
        rows=[{"task":"general","mode":"direct","rating":-1,"lesson":"Слишком длинно"},
              {"task":"general","mode":"direct","rating":-1,"lesson":" слишком  длинно "},
              {"task":"general","mode":"direct","rating":1,"lesson":"Хорошо"}]
        result=summarize(rows)
        self.assertEqual(result["repeated_lessons"],[{"lesson":"слишком длинно","count":2}])
        self.assertEqual(result["strategies"][0]["negative"],2)
        self.assertAlmostEqual(result["strategies"][0]["mean_rating"],-1/3)
        self.assertFalse(result["automatic_trait_change"])
    def test_empty(self):
        self.assertEqual(summarize([])["strategies"],[])
        self.assertEqual(summarize([])["repeated_lessons"],[])
