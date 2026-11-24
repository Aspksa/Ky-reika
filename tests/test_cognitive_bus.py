import tempfile
import unittest
from pathlib import Path
from core.database import initialize, add_message
from core.cognitive_bus import snapshot
from core.backup import refresh

class BusTests(unittest.TestCase):
    def test_changes_and_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"test.sqlite3"
            initialize(path)
            before=snapshot(path)
            add_message("user","test",path)
            after=snapshot(path)
            self.assertEqual(after["dialogue"],before.get("dialogue",0)+1)
            self.assertTrue(refresh(path).is_file())
