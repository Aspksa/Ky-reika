import tempfile
import unittest
from pathlib import Path
from core.resource_statistics import report

class ResourceStatisticsTests(unittest.TestCase):
    def test_report(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"test.sqlite3"
            path.write_bytes(b"abc")
            data=report(path)
            self.assertEqual(data["database_bytes"]["database"],3)
            self.assertGreaterEqual(data["uptime_seconds"],0)
            self.assertIsInstance(data["cloud_configured"],bool)
