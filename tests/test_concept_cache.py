import tempfile
import unittest
from pathlib import Path
from core import concepts, concept_relations, knowledge

class ConceptCacheTests(unittest.TestCase):
    def test_cache_reuse_and_invalidation(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"knowledge.sqlite3"
            for module in (concepts,concept_relations):
                module._cached.cache_clear()
                module.relevant("цвет",path)
                module.relevant("форма",path)
                self.assertEqual(module._cached.cache_info().hits,1)
            for subject in ("a","b","c"):
                knowledge.confirm(knowledge.propose(subject,"цвет","белый","test",path=path),path)
            for module in (concepts,concept_relations):
                module.relevant("цвет",path)
                self.assertEqual(module._cached.cache_info().misses,2)
            result=concepts.relevant("цвет",path)
            self.assertEqual(len(result),1)
            result[0]["examples"].clear()
            self.assertEqual(len(concepts.relevant("цвет",path)[0]["examples"]),3)
