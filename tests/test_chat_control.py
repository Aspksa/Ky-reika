import tempfile
import unittest
from pathlib import Path
from core.chat_control import command, execute
from core.database import recent_messages

class ChatControlTests(unittest.TestCase):
    def test_local_status(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"test.sqlite3"
            answer,response_id=execute("Состояние памяти?",path)
            self.assertIn("memories: 0",answer)
            self.assertEqual(recent_messages(2,path)[-1]["id"],response_id)
    def test_no_arbitrary_commands(self):
        self.assertIsNone(command("удали память"))
        self.assertIsNone(command("объясни состояние ядра"))
