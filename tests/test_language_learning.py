import tempfile
import unittest
from pathlib import Path
from core.database import initialize, add_message
from core.language_learning import refresh, candidates

class LanguageLearningTests(unittest.TestCase):
    def test_incremental(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"test.sqlite3"
            initialize(path)
            add_message("user","алгоритм алгоритм",path)
            add_message("user","алгоритм",path)
            add_message("assistant","алгоритм",path)
            self.assertEqual(refresh(path),2)
            self.assertEqual(refresh(path),0)
            self.assertEqual(candidates(path)[0]["occurrences"],2)
