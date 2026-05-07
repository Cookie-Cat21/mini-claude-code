import tempfile
import unittest
from pathlib import Path

from tools import TOOLS, execute_tool, tools_for_openai


class TestExecuteTool(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.td = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_read_write_file(self) -> None:
        p = self.td / "sub" / "x.txt"
        w = execute_tool("write_file", {"path": str(p), "content": "hello"})
        self.assertIn("Wrote 5 chars", w)
        r = execute_tool("read_file", {"path": str(p)})
        self.assertEqual(r, "hello")

    def test_read_missing(self) -> None:
        r = execute_tool("read_file", {"path": str(self.td / "nope.txt")})
        self.assertTrue(r.startswith("Error reading file:"))

    def test_bash_echo(self) -> None:
        r = execute_tool("bash", {"command": "echo ok"})
        self.assertEqual(r.strip(), "ok")

    def test_list_files(self) -> None:
        (self.td / "a.py").write_text("x", encoding="utf-8")
        (self.td / "b.py").write_text("y", encoding="utf-8")
        r = execute_tool("list_files", {"pattern": str(self.td / "*.py")})
        lines = set(r.splitlines())
        self.assertEqual(lines, {str(self.td / "a.py"), str(self.td / "b.py")})

    def test_unknown_tool(self) -> None:
        self.assertEqual(execute_tool("nope", {}), "Unknown tool: nope")


class TestToolsForOpenai(unittest.TestCase):
    def test_shape(self) -> None:
        oai = tools_for_openai()
        self.assertEqual(len(oai), len(TOOLS))
        for item in oai:
            self.assertEqual(item["type"], "function")
            self.assertIn("name", item["function"])
            self.assertIn("description", item["function"])
            self.assertIn("parameters", item["function"])
            self.assertEqual(item["function"]["parameters"]["type"], "object")


if __name__ == "__main__":
    unittest.main()
