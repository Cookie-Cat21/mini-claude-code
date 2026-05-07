"""Smoke tests for the Vercel-targeted FastAPI app (`api/index`)."""

import unittest

from starlette.testclient import TestClient


class TestApiIndexRoutes(unittest.TestCase):
    def test_get_root_is_not_legacy_html_shell(self) -> None:
        """SPA lives in ``public/``; this app must not own ``GET /``."""

        from api.index import app

        client = TestClient(app)
        r = client.get("/")
        self.assertEqual(r.status_code, 404)

    def test_get_assets_path_not_html(self) -> None:
        from api.index import app

        client = TestClient(app)
        r = client.get("/assets/index-deadbeef.js")
        self.assertEqual(r.status_code, 404)
        self.assertNotIn("text/html", r.headers.get("content-type", ""))

    def test_health(self) -> None:
        from api.index import app

        client = TestClient(app)
        r = client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"status": "ok"})

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
