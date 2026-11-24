import unittest
from core.dialogue_context import is_followup, messages

class DialogueContextTests(unittest.TestCase):
    def test_followup(self):
        self.assertTrue(is_followup("Делай и сливай"))
        self.assertTrue(is_followup("Дальше"))
        self.assertFalse(is_followup("Привет"))
    def test_roles(self):
        history=[{"role":"user","content":"Создай план"},{"role":"assistant","content":"План готов"}]
        result=messages("system","Делай",{"conversation_history":history})
        self.assertEqual([r["role"] for r in result],["system","user","assistant","user"])
        self.assertEqual(result[-1]["content"],"Делай")
