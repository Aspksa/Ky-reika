import os
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import URLError
from core import gateway
from core.context_budget import select

class StreamTests(unittest.TestCase):
    def test_retry_before_text(self):
        response=MagicMock()
        response.__enter__.return_value=iter([
            b'data: {"choices":[{"delta":{"content":"OK"}}]}\n',
            b'data: [DONE]\n'])
        stages=[]
        with patch.dict(os.environ,{"CLOUD_API_BASE":"https://example.com","CLOUD_API_KEY":"test","CLOUD_MODEL":"test"}), patch.object(gateway.reasoning,"prepare_dialogue",return_value={"strategy":{}}), patch("core.dialogue_style.profile",return_value={}), patch.object(gateway,"urlopen",side_effect=[URLError("offline"),response]) as call, patch.object(gateway,"sleep"), patch.object(gateway.reasoning,"finish") as finish, patch.object(gateway,"enqueue_learning"):
            self.assertEqual(list(gateway.stream_chat("test",progress=stages.append)),["OK"])
            self.assertEqual(call.call_count,2)
            finish.assert_called_once()
            self.assertIn("reconnecting",stages)

    def test_no_retry_after_text(self):
        def broken():
            yield b'data: {"choices":[{"delta":{"content":"OK"}}]}\n'
            raise ConnectionResetError()
        response=MagicMock()
        response.__enter__.return_value=broken()
        with patch.dict(os.environ,{"CLOUD_API_BASE":"https://example.com","CLOUD_API_KEY":"test","CLOUD_MODEL":"test"}), patch.object(gateway.reasoning,"prepare_dialogue",return_value={"strategy":{}}), patch("core.dialogue_style.profile",return_value={}), patch.object(gateway,"urlopen",return_value=response) as call, patch.object(gateway.reasoning,"finish") as finish:
            stream=gateway.stream_chat("test")
            self.assertEqual(next(stream),"OK")
            with self.assertRaises(ConnectionResetError):
                next(stream)
            call.assert_called_once()
            finish.assert_not_called()

    def test_context_and_budget(self):
        context={"dialogue_style":{"samples":3},"integral_intelligence":{"depth":"deep","methods":["causal"]},"causal_chains":[1]}
        selected=select("test",context)
        self.assertIn("dialogue_style",selected)
        self.assertIn("causal_chains",selected)
        self.assertEqual(gateway.token_budget("test",context),2048)
