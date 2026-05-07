"""Smoke tests for the Vercel-targeted FastAPI app (`api/index`)."""

import unittest

from starlette.testclient import TestClient


class TestApiIndexRoutes(unittest.TestCase):
    def test_root_and_aliases_return_html(self) -> None:
        from api.index import app

        client = TestClient(app)
        for path in ("/", "/api", "/api/", "/api/index"):
            with self.subTest(path=path):
                r = client.get(path)
                self.assertEqual(r.status_code, 200)
                self.assertIn("text/html", r.headers.get("content-type", ""))
                self.assertIn("mini-claude-code", r.text)

    def test_unknown_get_path_returns_shell(self) -> None:
        """Catch-all avoids FastAPI 404 when Vercel passes an unexpected scope path."""

        from api.index import app

        client = TestClient(app)
        r = client.get("/vercel-might-send-this")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/html", r.headers.get("content-type", ""))

    def test_post_chat_without_key_is_500_not_404(self) -> None:
        from api.index import app

        client = TestClient(app)
        r = client.post("/api/chat", json={"messages": [], "new_message": "hi"})
        self.assertEqual(r.status_code, 500)
        data = r.json()
        self.assertIn("GROQ_API_KEY", data.get("detail", ""))

    def test_post_api_index_aliases_to_chat(self) -> None:
        """When Vercel invokes POST on the function URL, path may be /api/index."""

        from api.index import app

        client = TestClient(app)
        r = client.post("/api/index", json={"messages": [], "new_message": "hi"})
        self.assertEqual(r.status_code, 500)
        data = r.json()
        self.assertIn("GROQ_API_KEY", data.get("detail", ""))


if __name__ == "__main__":
    unittest.main()
