import tempfile
import unittest
from pathlib import Path
from core.database import initialize, add_memory, list_memories, get_state
from core.personality import build_context

class TestCore(unittest.TestCase):
    def test_database(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.sqlite3"
            initialize(path)
            self.assertEqual(get_state(path)["mood"], "calm")
            add_memory("Проверка памяти", path=path)
            self.assertIn("Проверка памяти", build_context(path))
            self.assertEqual(len(list_memories(path=path)), 1)

if __name__ == "__main__":
    unittest.main()
