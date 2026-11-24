import unittest
from core.maintenance_runner import execute

class MaintenanceOrderTests(unittest.TestCase):
    def test_invalid_graph_has_no_side_effects(self):
        calls=[]
        with self.assertRaises(ValueError):
            execute([("a",lambda: calls.append(1),()),("b",lambda: None,("missing",))],None)
        self.assertEqual(calls,[])
    def test_failure_isolation(self):
        def fail():
            raise RuntimeError("test")
        result=execute([("a",fail,()),("b",lambda: self.fail("must skip"),("a",)),("c",lambda: None,())],None)
        self.assertEqual(result,{"a":"failed","b":"skipped_dependency","c":"ok"})
