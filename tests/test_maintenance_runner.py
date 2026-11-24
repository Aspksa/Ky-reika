import unittest
from core.maintenance_runner import execute

class MaintenanceTests(unittest.TestCase):
    def test_isolation_and_retry(self):
        calls=[]
        def fail():
            raise RuntimeError("test failure")
        stages=[("a",fail,()),("b",lambda:calls.append("b"),("a",)),
                ("c",lambda:calls.append("c"),())]
        with self.assertLogs("core.maintenance_runner",level="ERROR"):
            self.assertEqual(execute(stages,None),{"a":"failed","b":"skipped_dependency","c":"ok"})
        self.assertEqual(calls,["c"])
        stages[0]=("a",lambda:calls.append("a"),())
        self.assertEqual(execute(stages,None),{"a":"ok","b":"ok","c":"ok"})
        self.assertEqual(calls,["c","a","b","c"])
