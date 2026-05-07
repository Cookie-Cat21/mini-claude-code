import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import httpx

from agent_openai import _assistant_message_dict, _is_retryable, run_agent_openai
from openai import BadRequestError, InternalServerError, RateLimitError


class TestIsRetryable(unittest.TestCase):
    def test_rate_limit(self) -> None:
        req = httpx.Request("GET", "http://example.invalid")
        resp = httpx.Response(429, request=req)
        err = RateLimitError("limit", response=resp, body=None)
        self.assertTrue(_is_retryable(err))

    def test_server_error_503(self) -> None:
        req = httpx.Request("GET", "http://example.invalid")
        resp = httpx.Response(503, request=req)
        err = InternalServerError("down", response=resp, body=None)
        self.assertTrue(_is_retryable(err))

    def test_bad_request_400(self) -> None:
        req = httpx.Request("GET", "http://example.invalid")
        resp = httpx.Response(400, request=req)
        err = BadRequestError("bad", response=resp, body=None)
        self.assertFalse(_is_retryable(err))


class TestAssistantMessageDict(unittest.TestCase):
    def test_text_only(self) -> None:
        msg = mock.Mock()
        msg.content = "Hi"
        msg.tool_calls = None
        d = _assistant_message_dict(msg)
        self.assertEqual(d, {"role": "assistant", "content": "Hi"})

    def test_with_tools(self) -> None:
        fn = mock.Mock()
        fn.name = "read_file"
        fn.arguments = '{"path": "/tmp/x"}'
        tc = mock.Mock()
        tc.id = "id1"
        tc.function = fn
        msg = mock.Mock()
        msg.content = None
        msg.tool_calls = [tc]
        d = _assistant_message_dict(msg)
        self.assertEqual(d["role"], "assistant")
        self.assertEqual(len(d["tool_calls"]), 1)
        self.assertEqual(d["tool_calls"][0]["id"], "id1")
        self.assertEqual(d["tool_calls"][0]["function"]["name"], "read_file")


class TestRunAgentOpenai(unittest.TestCase):
    def test_empty_configs(self) -> None:
        with self.assertRaises(ValueError):
            run_agent_openai([], [], "")

    @mock.patch("agent_openai.OpenAI")
    @mock.patch("agent_openai.random.randrange", return_value=0)
    def test_text_response(self, _rand, mock_openai_cls) -> None:
        mock_client = mock.Mock()
        mock_openai_cls.return_value = mock_client

        msg = mock.Mock()
        msg.content = "  All good.  "
        msg.tool_calls = None
        mock_client.chat.completions.create.return_value = mock.Mock(choices=[mock.Mock(message=msg)])

        messages: list = [{"role": "user", "content": "Hello"}]
        out = run_agent_openai([("https://api.example/v1", "key", "model-x")], messages, "You are helpful.")

        self.assertEqual(out, "All good.")
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[-1], {"role": "assistant", "content": "  All good.  "})

    @mock.patch("builtins.print")
    @mock.patch("agent_openai.OpenAI")
    @mock.patch("agent_openai.random.randrange", return_value=0)
    def test_tool_then_text(self, _rand, mock_openai_cls, _print) -> None:
        td = tempfile.TemporaryDirectory()
        try:
            fp = Path(td.name) / "t.txt"
            fp.write_text("orig", encoding="utf-8")

            mock_client = mock.Mock()
            mock_openai_cls.return_value = mock_client

            fn = mock.Mock()
            fn.name = "read_file"
            fn.arguments = json.dumps({"path": str(fp)})
            tc = mock.Mock()
            tc.id = "call_abc"
            tc.function = fn

            msg_tool = mock.Mock()
            msg_tool.content = None
            msg_tool.tool_calls = [tc]

            msg_done = mock.Mock()
            msg_done.content = "File says orig"
            msg_done.tool_calls = None

            mock_client.chat.completions.create.side_effect = [
                mock.Mock(choices=[mock.Mock(message=msg_tool)]),
                mock.Mock(choices=[mock.Mock(message=msg_done)]),
            ]

            messages = [{"role": "user", "content": "Read it"}]
            out = run_agent_openai([("https://api.example/v1", "k", "m")], messages, "")

            self.assertEqual(out, "File says orig")
            self.assertEqual(mock_client.chat.completions.create.call_count, 2)
            # user + assistant with tools + tool result + assistant final
            roles = [m["role"] for m in messages]
            self.assertEqual(roles, ["user", "assistant", "tool", "assistant"])
        finally:
            td.cleanup()

    @mock.patch("agent_openai.OpenAI")
    @mock.patch("agent_openai.random.randrange", return_value=0)
    def test_failover_second_key(self, _rand, mock_openai_cls) -> None:
        req = httpx.Request("GET", "http://example.invalid")
        resp429 = httpx.Response(429, request=req)
        rate_err = RateLimitError("rl", response=resp429, body=None)

        def make_client(*_a, **kwargs):
            c = mock.Mock()
            if kwargs.get("api_key") == "key1":
                c.chat.completions.create.side_effect = rate_err
            else:
                msg = mock.Mock()
                msg.content = "recovered"
                msg.tool_calls = None
                c.chat.completions.create.return_value = mock.Mock(choices=[mock.Mock(message=msg)])
            return c

        mock_openai_cls.side_effect = make_client

        messages = [{"role": "user", "content": "Hi"}]
        out = run_agent_openai(
            [
                ("https://api.groq.com/openai/v1", "key1", "m"),
                ("https://api.groq.com/openai/v1", "key2", "m"),
            ],
            messages,
            "",
        )
        self.assertEqual(out, "recovered")


if __name__ == "__main__":
    unittest.main()
