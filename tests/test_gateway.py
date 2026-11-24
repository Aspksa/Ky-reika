import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from core import gateway
from core.database import recent_messages

class GatewayTests(unittest.TestCase):
    def test_chat_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"test.sqlite3"
            with patch.dict(os.environ,{"CLOUD_MODEL":"test","CLOUD_EMBED_MODEL":"","CLOUD_REVIEW_ANSWERS":"0","CLOUD_EXTRACT_FACTS":"0"}):
                with patch.object(gateway,"request",return_value={"choices":[{"message":{"content":"Ответ"}}]}) as request:
                    self.assertEqual(gateway.chat("Вопрос",path),"Ответ")
                    endpoint,payload=request.call_args.args
                    self.assertEqual(endpoint,"/chat/completions")
                    self.assertEqual(payload["messages"][-1]["content"],"Вопрос")
                    self.assertIn("metalogic",payload["messages"][0]["content"])
                self.assertEqual([r["role"] for r in recent_messages(10,path)],["user","assistant"])
                with patch.object(gateway,"request",side_effect=TimeoutError):
                    with self.assertRaises(TimeoutError):
                        gateway.chat("Ошибка",path)
                self.assertEqual(len(recent_messages(10,path)),2)
