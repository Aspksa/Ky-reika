import unittest
from core.language_context import analyze

class LanguageContextTests(unittest.TestCase):
    def test_original_offsets(self):
        message="Не удаляй Wi-Fi, продолжай!"
        result=analyze(message)
        self.assertTrue(result["negation_present"])
        for token in result["tokens"]:
            self.assertEqual(message[token["start"]:token["end"]],token["text"])
    def test_followup(self):
        result=analyze("Делай",[{"role":"user","content":"Обнови исследования"}])
        self.assertEqual(result["previous_user_request"],"Обнови исследования")
