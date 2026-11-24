import unittest
from unittest.mock import patch
from core.morphology import matches, lemma

class MorphologyTests(unittest.TestCase):
    def test_fallback(self):
        with patch("core.morphology.analyzer",return_value=None):
            lemma.cache_clear()
            self.assertTrue(matches("ядро","состояние ядро"))
            self.assertFalse(matches("ядро","ядрообразный"))
            lemma.cache_clear()
