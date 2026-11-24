import tempfile
import unittest
from pathlib import Path
from core.database import initialize
from core.statistics import report, snapshot, history

class StatisticsTests(unittest.TestCase):
    def test_history(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"test.sqlite3"
            initialize(path)
            self.assertEqual(report(path)["metrics"]["messages"],0)
            snapshot(path)
            self.assertEqual(history(path)[-1]["metrics"]["messages"],0)
