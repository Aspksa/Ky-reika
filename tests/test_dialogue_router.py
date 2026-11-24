import unittest
from core.dialogue_router import route

class DialogueRouterTests(unittest.TestCase):
    def test_social(self):
        self.assertEqual(route("Кто я для тебя?"),"social")
    def test_definition(self):
        self.assertEqual(route("Что такое фотосинтез?"),"standard")
    def test_complex(self):
        self.assertEqual(route("Что такое причина ошибки?"),"deep")
        self.assertEqual(route("Что означает это?"),"deep")
        self.assertEqual(route("Что такое атом?\nСравни модели"),"deep")
    def test_followup(self):
        history=[{"role":"user","content":"Проанализируй систему"},{"role":"assistant","content":"Описание"}]
        self.assertEqual(route("Что такое модуль?",history),"deep")
