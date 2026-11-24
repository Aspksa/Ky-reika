import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from core.chat_tasks import enqueue, process, recent

class ChatTaskTests(unittest.TestCase):
    def test_queue(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"test.sqlite3"
            task=enqueue(path,"learning")
            self.assertEqual(recent(path)[0]["status"],"pending")
            with patch("core.learning_review.refresh") as action:
                process(path)
                action.assert_called_once_with(path)
            self.assertEqual(recent(path)[0]["id"],task)
            self.assertEqual(recent(path)[0]["status"],"done")
    def test_unknown(self):
        with self.assertRaises(ValueError):
            enqueue("unused","shell")
