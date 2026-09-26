"""Walking-skeleton API tests: one happy path through every layer.

- GET /api/profile returns the ok envelope parsed fresh from content/profile.md.
- GET / returns the SPA index.html (StaticFiles mount registered AFTER /api routes).
"""

from fastapi.testclient import TestClient

from app.config import FRONTEND_DIST
from app.main import app

client = TestClient(app)


def test_get_profile_returns_ok_envelope() -> None:
    resp = client.get("/api/profile")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["exemplo"] is True  # shipped file ships as example data (D-11)
    assert body["perfil"]["name"]  # parsed profile object is present


def test_get_serves_spa_index_html() -> None:
    if not FRONTEND_DIST.exists():
        raise AssertionError(
            "frontend/dist ausente — rode 'cd frontend && npm run build' antes dos testes (README)"
        )
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
