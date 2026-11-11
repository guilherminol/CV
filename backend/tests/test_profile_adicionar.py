"""POST /api/profile/adicionar — accept JD keywords into the owner's profile.

Pinned here: the ok envelope (same shape as GET + adicionado/ja_existentes);
skill groups created on first add; casefold dedup; name-only certifications;
the erro envelope when the profile file is broken; and the write path NEVER
touching the real content/profile.md (tests retarget PROFILE_PATH the same
way test_api does).
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture()
def perfil_tmp(monkeypatch, tmp_path):
    """A minimal valid profile.md in tmp_path + the loader pointed at it."""
    path = tmp_path / "profile.md"
    path.write_text(
        "---\n"
        'name: "Ana Exemplo"\n'
        "contact:\n"
        '  email: "ana@example.com"\n'
        "summary:\n"
        '  pt-BR: "Resumo."\n'
        '  en: "Summary."\n'
        "experiences:\n"
        "  - company: \"Exemplo IA\"\n"
        "    title:\n"
        '      pt-BR: "Engenheira"\n'
        '      en: "Engineer"\n'
        '    start_date: "2022-03"\n'
        "    description:\n"
        '      pt-BR: "Descrição."\n'
        '      en: "Description."\n'
        "    impacts: []\n"
        "skills:\n"
        "  - category: \"Linguagens\"\n"
        "    items: [\"Python\"]\n"
        "---\n\n"
        "Perfil de teste.\n",
        encoding="utf-8",
    )
    import app.profile.loader as loader_module

    monkeypatch.setattr(loader_module, "PROFILE_PATH", path)
    return path


def _adicionar(adicoes: list[dict]) -> dict:
    resp = client.post("/api/profile/adicionar", json={"adicoes": adicoes})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_adiciona_ferramenta_criando_grupo(perfil_tmp) -> None:
    body = _adicionar(
        [{"canonical": "Terraform", "pt": "Terraform", "en": "Terraform", "categoria": "ferramentas"}]
    )
    assert body["status"] == "ok"
    assert body["adicionado"] == ["Terraform"]
    assert body["ja_existentes"] == []
    grupos = {g["category"]: g["items"] for g in body["perfil"]["skills"]}
    assert grupos["Ferramentas"] == ["Terraform"]
    # The file itself re-reads fresh on GET (D-15) — the write really landed.
    depois = client.get("/api/profile").json()
    grupos_get = {g["category"]: g["items"] for g in depois["perfil"]["skills"]}
    assert grupos_get["Ferramentas"] == ["Terraform"]


def test_dedup_casefold_manda_para_ja_existentes(perfil_tmp) -> None:
    primeira = _adicionar(
        [{"canonical": "Kubernetes", "pt": "Kubernetes", "en": "Kubernetes", "categoria": "ferramentas"}]
    )
    assert primeira["adicionado"] == ["Kubernetes"]
    segunda = _adicionar(
        [{"canonical": "kubernetes", "pt": "kubernetes", "en": "kubernetes", "categoria": "ferramentas"}]
    )
    assert segunda["adicionado"] == []
    assert segunda["ja_existentes"] == ["kubernetes"]
    grupos = {g["category"]: g["items"] for g in segunda["perfil"]["skills"]}
    assert grupos["Ferramentas"] == ["Kubernetes"]


def test_competencias_e_certificacao(perfil_tmp) -> None:
    body = _adicionar(
        [
            {
                "canonical": "Advanced RAG",
                "pt": "RAG avançado",
                "en": "Advanced RAG",
                "categoria": "competencias",
            },
            {
                "canonical": "AWS Certified Solutions Architect",
                "pt": None,
                "en": "AWS Certified Solutions Architect",
                "categoria": "certificacoes",
            },
        ]
    )
    assert body["adicionado"] == ["RAG avançado", "AWS Certified Solutions Architect"]
    grupos = {g["category"]: g["items"] for g in body["perfil"]["skills"]}
    assert grupos["Competências"] == ["RAG avançado"]
    # Name-only entry — issuer/year stay for the owner to complete by hand.
    assert body["perfil"]["certifications"] == [
        {"name": "AWS Certified Solutions Architect", "issuer": None, "year": None}
    ]


def test_dedup_ambito_por_secao(perfil_tmp) -> None:
    """A name already in skills does not block the same name as a certification
    (and vice versa) — the sections are independent lists."""
    _adicionar(
        [{"canonical": "Terraform", "pt": "Terraform", "en": "Terraform", "categoria": "ferramentas"}]
    )
    body = _adicionar(
        [{"canonical": "Terraform Associate", "pt": "Terraform Associate", "en": None, "categoria": "certificacoes"}]
    )
    assert body["adicionado"] == ["Terraform Associate"]


def test_exemplo_flag_e_completude_no_envelope(perfil_tmp) -> None:
    body = _adicionar(
        [{"canonical": "Docker", "pt": "Docker", "en": "Docker", "categoria": "ferramentas"}]
    )
    assert body["exemplo"] is False
    assert body["completude"]["habilidades"] is True
    assert body["completude"]["habilidades_itens_qtde"] == 2  # Python + Docker


def test_perfil_quebrado_da_envelope_erro(monkeypatch, tmp_path) -> None:
    broken = tmp_path / "profile.md"
    broken.write_text("---\nname: \"Ana\"\n---\n\ncorpo\n", encoding="utf-8")
    import app.profile.loader as loader_module

    monkeypatch.setattr(loader_module, "PROFILE_PATH", broken)
    resp = client.post(
        "/api/profile/adicionar",
        json={"adicoes": [{"canonical": "X", "pt": "X", "en": "X", "categoria": "ferramentas"}]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "erro"
    assert body["erros"]


def test_sem_adicoes_rejeita_422(perfil_tmp) -> None:
    resp = client.post("/api/profile/adicionar", json={"adicoes": []})
    assert resp.status_code == 422  # client bug, not a UI state (regen dica convention)


def test_categoria_titulos_rejeita_422(perfil_tmp) -> None:
    """Job titles have no profile home — the request model rejects them."""
    resp = client.post(
        "/api/profile/adicionar",
        json={"adicoes": [{"canonical": "Tech Lead", "pt": None, "en": None, "categoria": "titulos_de_vaga"}]},
    )
    assert resp.status_code == 422
