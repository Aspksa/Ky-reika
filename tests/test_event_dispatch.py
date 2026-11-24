import tempfile
import unittest
from pathlib import Path
from core.database import initialize, add_message
from core.event_dispatch import run_if_changed

class EventDispatchTests(unittest.TestCase):
    def test_retry_and_ack(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"test.sqlite3"
            initialize(path)
            calls=[]
            def action():
                calls.append(1)
            def fail():
                raise RuntimeError("test")
            with self.assertRaises(RuntimeError):
                run_if_changed(path,"test",("dialogue",),fail)
            self.assertTrue(run_if_changed(path,"test",("dialogue",),action))
            self.assertFalse(run_if_changed(path,"test",("dialogue",),action))
            add_message("user","new",path)
            self.assertTrue(run_if_changed(path,"test",("dialogue",),action))
            self.assertEqual(len(calls),2)
