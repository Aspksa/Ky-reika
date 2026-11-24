import unittest
from core.personality_review import inspect

class PersonalityReviewTests(unittest.TestCase):
    def test_explicit_claims(self):
        self.assertEqual(inspect("Я настоящий человек."),["physical_identity_claim"])
        self.assertEqual(inspect("У меня нет долговременной памяти."),["memory_denial"])
    def test_normal_dialogue(self):
        self.assertEqual(inspect("Я Кюрейка, рада тебя видеть."),[])
        self.assertEqual(inspect("У меня нет памяти об этом событии."),[])
        self.assertEqual(inspect("Ты сказал: «Я настоящий человек»."),[])
