import os
import unittest
from unittest import mock

from fastapi.testclient import TestClient


class TestServer(unittest.TestCase):
    def test_health(self) -> None:
        from fly_server import app

        c = TestClient(app)
        r = c.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"status": "ok"})

    @mock.patch("fly_server.resolve_backend", return_value=("openai", [("https://x", "k", "m")]))
    def test_meta_openai(self, _rb) -> None:
        from fly_server import app

        c = TestClient(app)
        r = c.get("/meta")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["chat_stream"])

    @mock.patch("fly_server.resolve_backend", return_value=("anthropic", None))
    def test_meta_anthropic(self, _rb) -> None:
        from fly_server import app

        c = TestClient(app)
        r = c.get("/meta")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["chat_stream"])

    @mock.patch("fly_server.run_agent_openai", return_value="hello")
    @mock.patch("fly_server.resolve_backend", return_value=("openai", [("https://x", "k", "m")]))
    def test_chat_sync(self, _rb, _run) -> None:
        from fly_server import app

        c = TestClient(app)
        r = c.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["text"], "hello")
        self.assertEqual(r.json()["messages"][-1]["role"], "user")

    @mock.patch("fly_server.resolve_backend", return_value=("openai", [("https://x", "k", "m")]))
    def test_chat_rejects_anthropic_blocks(self, _rb) -> None:
        from fly_server import app

        c = TestClient(app)
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "tool_use", "name": "read_file", "id": "x", "input": {}}],
                }
            ]
        }
        r = c.post("/chat", json=body)
        self.assertEqual(r.status_code, 422)
        self.assertIn("OpenAI-style", r.json()["detail"])

    @mock.patch("fly_server.resolve_backend", return_value=("openai", [("https://x", "k", "m")]))
    def test_chat_secret_401(self, _rb) -> None:
        from fly_server import app

        with mock.patch.dict(os.environ, {"CHAT_API_SECRET": "s3cr3t"}):
            c = TestClient(app)
            r = c.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]})
            self.assertEqual(r.status_code, 401)


if __name__ == "__main__":
    unittest.main()
