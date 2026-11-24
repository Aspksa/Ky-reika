import unittest
from core.knowledge_transfer import suggest

class TransferTests(unittest.TestCase):
    def test_method_transfer_never_authorizes_fact_transfer(self):
        lesson={"id":"a","revision":1,"observable":["device","state","on"],
                "status":"contradicting_observation","sources":[1],"guidance":"Check assumptions"}
        context={"prediction_learning":{"lessons":[lesson]},"metalogic":{"methods":["causal"]}}
        result=suggest("why does a plant wilt",context)
        self.assertEqual(result[0]["match"],"method_only")
        self.assertFalse(result[0]["factual_transfer_authorized"])
        self.assertEqual(suggest("hello",{"prediction_learning":{"lessons":[lesson]}}),[])
        lesson["status"]="awaiting_observation"
        self.assertEqual(suggest("device",context),[])
