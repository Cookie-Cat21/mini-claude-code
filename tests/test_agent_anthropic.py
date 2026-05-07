import unittest
from unittest import mock

from agent import _text_from_assistant_content, run_agent_anthropic


class _TextBlock:
    type = "text"

    def __init__(self, text: str) -> None:
        self.text = text


class TestTextFromContent(unittest.TestCase):
    def test_joins_text_blocks(self) -> None:
        blocks = [_TextBlock("Hello "), _TextBlock("world")]
        self.assertEqual(_text_from_assistant_content(blocks), "Hello world")


class TestRunAgentAnthropic(unittest.TestCase):
    @mock.patch("agent.execute_tool")
    def test_max_tokens_returns_partial_without_empty_tool_user(self, mock_exec) -> None:
        client = mock.Mock()
        text_block = _TextBlock("Partial answer")
        turn = mock.Mock()
        turn.stop_reason = "max_tokens"
        turn.content = [text_block]
        client.messages.create.return_value = turn

        messages: list = [{"role": "user", "content": "Hi"}]
        out = run_agent_anthropic(client, messages, "", max_tool_rounds=5)

        self.assertEqual(out, "Partial answer")
        mock_exec.assert_not_called()
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[-1]["role"], "assistant")

    @mock.patch("agent.execute_tool")
    def test_tool_use_then_end_turn(self, mock_exec) -> None:
        client = mock.Mock()

        class _Tool:
            type = "tool_use"

            def __init__(self, name: str, id_: str, input_: dict) -> None:
                self.name = name
                self.id = id_
                self.input = input_

        t1 = _Tool("read_file", "tu1", {"path": "/x"})
        r1 = mock.Mock()
        r1.stop_reason = "tool_use"
        r1.content = [t1]

        r2 = mock.Mock()
        r2.stop_reason = "end_turn"
        r2.content = [_TextBlock("Done.")]

        mock_exec.return_value = "file contents"
        client.messages.create.side_effect = [r1, r2]

        messages: list = [{"role": "user", "content": "Read /x"}]
        out = run_agent_anthropic(client, messages, "", max_tool_rounds=10)

        self.assertEqual(out, "Done.")
        mock_exec.assert_called_once_with("read_file", {"path": "/x"})
        self.assertEqual(client.messages.create.call_count, 2)
        self.assertEqual(messages[-1]["role"], "assistant")

    def test_max_rounds_guard(self) -> None:
        client = mock.Mock()
        t_block = type("T", (), {"type": "tool_use", "name": "bash", "id": "1", "input": {"command": "true"}})()
        turn = mock.Mock()
        turn.stop_reason = "tool_use"
        turn.content = [t_block]
        client.messages.create.return_value = turn

        with mock.patch("agent.execute_tool", return_value="ok"):
            messages = [{"role": "user", "content": "x"}]
            with self.assertRaises(RuntimeError) as ctx:
                run_agent_anthropic(client, messages, "", max_tool_rounds=2)
        self.assertIn("maximum agent steps", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
