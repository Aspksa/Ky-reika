import unittest
from core.method_library import gate_transfer

class MethodGateTests(unittest.TestCase):
    def test_failed_transfer(self):
        self.assertIsNone(gate_transfer({"status":"validated","method":{"indexed":True}},{"status":"transfer_failed"})["method"])
    def test_passed_transfer(self):
        selection={"status":"validated","method":{"indexed":True}}
        self.assertEqual(gate_transfer(selection,{"status":"transfer_validated","method":selection["method"]}),selection)
