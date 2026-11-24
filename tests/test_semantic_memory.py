import tempfile
import unittest
from pathlib import Path
from core.chat_control import execute
from core.semantic_memory import relevant

class SemanticMemoryTests(unittest.TestCase):
    def test_definition_and_correction(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"test.sqlite3"
            execute('Запомни значение «лиса»: имя проекта',path)
            self.assertEqual(relevant("Лиса",path)[0]["meaning"],"имя проекта")
            execute('Уточни значение «лиса»: кодовое имя',path)
            self.assertEqual(relevant("лиса",path)[0]["meaning"],"кодовое имя")
            self.assertEqual(relevant("лисам",path),[])
