import unittest
from core.personality_experience import evaluate

class PersonalityExperienceTests(unittest.TestCase):
    def test_threshold_and_conflict(self):
        rows=[{"message_id":i,"lesson":"Отвечай короче"} for i in (3,2,1)]
        self.assertEqual(evaluate(rows[:2])["preferences"],{})
        self.assertEqual(evaluate(rows)["preferences"]["length"]["preference"],"concise")
        self.assertEqual(evaluate([{"message_id":4,"lesson":"Отвечай подробнее"}]+rows)["preferences"],{})
        self.assertTrue(evaluate(rows)["core_traits_unchanged"])
