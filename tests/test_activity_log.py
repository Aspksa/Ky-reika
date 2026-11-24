import sqlite3
import unittest
from core.activity_log import append,recent

class ActivityTests(unittest.TestCase):
    def test_recent(self):
        with sqlite3.connect(":memory:") as db:
            db.row_factory=sqlite3.Row
            self.assertEqual(recent(db),[])
            append(db,"stage","training","ok")
            append(db,"metric","words","changed",3)
            self.assertEqual(recent(db)[0]["delta"],3)
            self.assertEqual(recent(db)[1]["subject"],"training")
