"""Walking-skeleton API tests: one happy path through every layer.

- GET /api/profile returns the ok envelope parsed fresh from content/profile.md,
  including the completude section map (D-12).
- A broken profile yields the erro envelope naming the exact key in PT-BR,
  never an HTTP 500; raw detail goes to the terminal log only (SC2/D-13).
- GET / returns the SPA index.html (StaticFiles mount registered AFTER /api routes).
"""

import logging

import pytest
from fastapi.testclient import TestClient

from app.config import FRONTEND_DIST
from app.main import app

client = TestClient(app)


def test_get_profile_returns_ok_envelope() -> None:
    resp = client.get("/api/profile")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    # The shipped file is the owner's LIVE profile — example flips to False the
    # moment real data lands (D-11); the envelope shape is the contract here.
    assert isinstance(body["exemplo"], bool)
    assert body["perfil"]["name"]  # parsed profile object is present
    assert body["perfil"]["experiences"]  # SC3 data half: experiences present


def test_get_profile_ok_envelope_includes_completude() -> None:
    body = client.get("/api/profile").json()
    assert body["status"] == "ok"
    completude = body["completude"]
    perfil = body["perfil"]
    # Counts stay consistent with the shipped profile itself — the file is
    # owner-edited data, never a pinned persona (hardcoded counts rotted the
    # moment real data replaced the example).
    assert completude["resumo"] is True
    assert completude["experiencias"] is True
    assert completude["experiencias_qtde"] == len(perfil["experiences"])
    assert completude["habilidades"] is True
    assert completude["habilidades_qtde"] == len(perfil["skills"])
    assert completude["idiomas_qtde"] == len(perfil["languages"])
    assert completude["projetos_qtde"] == len(perfil["projects"])


def _use_profile_file(monkeypatch: pytest.MonkeyPatch, path) -> None:
    import app.profile.loader as loader_module

    monkeypatch.setattr(loader_module, "PROFILE_PATH", path)


def test_get_profile_erro_envelope_names_exact_key(monkeypatch, tmp_path) -> None:
    broken = tmp_path / "profile.md"
    broken.write_text(
        "---\nname: \"Ana\"\ncontact:\n  email: \"a@b.c\"\n"
        "summary:\n  pt-BR: \"r\"\nexperiances: []\n---\n",
        encoding="utf-8",
    )
    _use_profile_file(monkeypatch, broken)
    resp = client.get("/api/profile")
    assert resp.status_code == 200  # a broken profile is a UI state, never a 500 (D-12)
    body = resp.json()
    assert body["status"] == "erro"
    assert any(
        "experiances" in line and "chave desconhecida" in line for line in body["erros"]
    )


def test_get_profile_erro_envelope_on_broken_yaml(monkeypatch, tmp_path) -> None:
    broken = tmp_path / "profile.md"
    broken.write_text("---\nname: [unclosed\n---\n", encoding="utf-8")
    _use_profile_file(monkeypatch, broken)
    body = client.get("/api/profile").json()
    assert body["status"] == "erro"
    assert any("YAML do frontmatter inválido" in line for line in body["erros"])
    assert any(str(broken) in line for line in body["erros"])  # the exact file is named


def test_erro_raw_detail_goes_to_terminal_log_only(monkeypatch, tmp_path, caplog) -> None:
    broken = tmp_path / "profile.md"
    broken.write_text(
        "---\nname: \"Ana\"\ncontact:\n  email: \"a@b.c\"\n"
        "summary:\n  pt-BR: \"r\"\nexperiances: []\n---\n",
        encoding="utf-8",
    )
    _use_profile_file(monkeypatch, broken)
    with caplog.at_level(logging.ERROR, logger="app.routes.profile"):
        body = client.get("/api/profile").json()
    assert body["status"] == "erro"
    # raw pydantic detail in the terminal log (D-13)...
    terminal_text = " ".join(rec.getMessage() for rec in caplog.records)
    assert "extra_forbidden" in terminal_text
    # ...but never in the API envelope (T-01-07)
    assert "extra_forbidden" not in " ".join(body["erros"])


def test_get_serves_spa_index_html() -> None:
    if not FRONTEND_DIST.exists():
        raise AssertionError(
            "frontend/dist ausente — rode 'cd frontend && npm run build' antes dos testes (README)"
        )
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
