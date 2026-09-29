"""Per-section regeneration pipeline tests — run_section_regen +
compose_regen_stage_input (plan 05-01, SC1/D-05/D-06/D-07/D-15), OFFLINE.

Pinned here, via a ScriptedClient recording every create() kwargs (copied
verbatim from tests/test_resume_pipeline.py, D-16 house pattern) and a
retargeted PROFILE_PATH (D-15 seam):

- (a) exactly ONE gateway stage runs per regen — the section's own stage
  (SECTION_STAGE_BY_ID); keyword extraction and sibling stages never run;
- (b) hint-as-DATA: an optional dica appears ONLY inside the composed user
  message (messages[1]); the system message (messages[0]) is the untouched
  prompt-file body for that stage; the SDK create() field set is unchanged
  and runs.jsonl stays metadata-only — the hint text never reaches it
  (T-05-04, D-15);
- (c) sibling byte-identity: only the target key is replaced in the merged
  secoes — sibling values come back equal (== and same string objects) to
  what was submitted (D-07/SC1);
- (d) coverage is recomputed over the FULL merged generated text — a keyword
  that appears only in a submitted sibling AND one that appears only in the
  new section both come back coberto (D-07);
- (e) blank/None dica is normalized away at the compose boundary — the user
  message equals the plain compose_stage_input composition.
"""

import json
from pathlib import Path

import pytest

from app.llm.gateway import load_prompt
from app.llm.schemas import ExperienciaGerada, Keyword
from app.profile.models import Profile
from app.resume.facts import compose_stage_input, serialize_profile_facts
from app.routes.export import ExportarSecoes
from conftest import full_profile

# ---------------------------------------------------------------------------
# Offline fakes — copied verbatim from tests/test_resume_pipeline.py (D-16)
# ---------------------------------------------------------------------------


class _FakeUsage:
    prompt_tokens = 120
    completion_tokens = 80
    total_tokens = 200


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [type("Choice", (), {"message": type("Msg", (), {"content": content})()})()]
        self.usage = _FakeUsage()
        self.cost = None


class ScriptedClient:
    """Fake returning a scripted SEQUENCE of contents / exceptions — one per
    attempt — recording every create() call."""

    def __init__(self, script: list):
        self._script = list(script)
        self.calls: list[dict] = []
        chat = type("Chat", (), {})()
        completions = type("Completions", (), {})()

        def create(**kwargs):
            self.calls.append(kwargs)
            item = self._script.pop(0)
            if isinstance(item, Exception):
                raise item
            return _FakeResponse(item)

        completions.create = create
        chat.completions = completions
        self.chat = chat


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Offline suite: a fake key satisfies the call-time guard (D-16)."""
    monkeypatch.setattr("app.llm.gateway.OPENROUTER_API_KEY", "test-key-offline")


# ---------------------------------------------------------------------------
# Canned content (UTF-8 accents survive the JSON round-trip) + shared inputs
# ---------------------------------------------------------------------------

JD_REGEN = (
    "Vaga: engenheiro(a) de dados sênior. Requisitos: experiência com Python, "
    "Docker e pipelines de dados em produção. Diferencial: certificação AWS."
)

KEYWORDS_CONTENT = json.dumps(
    {
        "keywords": [
            {
                "canonical": "Python",
                "aliases": [],
                "pt": "Python",
                "en": "Python",
                "category": "competencias",
            },
            {
                "canonical": "Docker",
                "aliases": [],
                "pt": "Docker",
                "en": "Docker",
                "category": "ferramentas",
            },
        ]
    },
    ensure_ascii=False,
)

NEW_RESUMO_CONTENT = json.dumps(
    {"resumo": "Nova síntese gerada para o resumo, citando Docker e observabilidade."},
    ensure_ascii=False,
)

NEW_EXPERIENCIAS_CONTENT = json.dumps(
    {
        "experiencias": [
            {
                "company": "Exemplo IA",
                "title": "Engenheira de Software Sênior",
                "bullets": ["Novo bullet gerado com Docker e métricas de impacto"],
            }
        ]
    },
    ensure_ascii=False,
)

NEW_SKILLS_CONTENT = json.dumps(
    {"habilidades": ["Python", "Docker", "FastAPI"]},
    ensure_ascii=False,
)

# secao → (gateway stage, canned regen output for that stage)
REGEN_TARGETS = [
    ("resumo", "resume-summary", "resume_summary", NEW_RESUMO_CONTENT),
    ("experiencias", "resume-experiencias", "resume_experiencias", NEW_EXPERIENCIAS_CONTENT),
    ("habilidades", "resume-skills", "resume_skills", NEW_SKILLS_CONTENT),
]


def _keywords() -> list[Keyword]:
    payload = json.loads(KEYWORDS_CONTENT)
    return [Keyword.model_validate(item) for item in payload["keywords"]]


def _submitted() -> ExportarSecoes:
    """The displayed state a client would re-post: a sibling resumo carrying
    "Python", an experience entry WITHOUT either keyword, and a stale
    habilidades list that the regen replaces."""
    return ExportarSecoes(
        resumo="Resumo em exibição com Python e histórico de dados.",
        experiencias=[
            ExperienciaGerada(
                company="Exemplo IA",
                title="Engenheira de Software Sênior",
                bullets=["Atuou em pipelines de dados internos"],
            )
        ],
        habilidades=["Habilidade antiga"],
    )


@pytest.fixture
def _profile_path(monkeypatch: pytest.MonkeyPatch, valid_profile_path: Path) -> None:
    """Loader seam: load_profile() re-resolves PROFILE_PATH at call time (D-15)."""
    monkeypatch.setattr("app.profile.loader.PROFILE_PATH", valid_profile_path)


# ---------------------------------------------------------------------------
# (a) Exactly ONE stage per regen — the section's own stage (D-06, SC1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("secao", "stage", "_wire", "content"), REGEN_TARGETS)
def test_run_section_regen_runs_exactly_one_stage(
    secao: str,
    stage: str,
    _wire: str,
    content: str,
    tmp_path: Path,
    _profile_path: None,
) -> None:
    from app.resume.pipeline import run_section_regen

    client = ScriptedClient([content])
    envelope = run_section_regen(
        JD_REGEN,
        "pt-BR",
        secao,
        _submitted(),
        _keywords(),
        runs_log=tmp_path / "runs.jsonl",
        client=client,
    )
    assert len(client.calls) == 1  # extraction + siblings NEVER run (D-06)
    assert client.calls[0]["response_format"]["json_schema"]["name"] == _wire
    assert client.calls[0]["response_format"]["json_schema"]["strict"] is True
    assert envelope["status"] == "ok"
    assert envelope["idioma"] == "pt-BR"
    assert set(envelope) == {"status", "idioma", "secoes", "cobertura", "cobertura_resumo"}


# ---------------------------------------------------------------------------
# (b) Hint-as-DATA — user message only; system prompt + runs.jsonl untouched
# ---------------------------------------------------------------------------


def test_dica_travels_as_user_message_data_system_and_log_untouched(
    tmp_path: Path, _profile_path: None
) -> None:
    from app.resume.pipeline import run_section_regen

    dica = "destacar experiência com métricas de impacto"
    runs_log = tmp_path / "runs.jsonl"
    client = ScriptedClient([NEW_SKILLS_CONTENT])
    run_section_regen(
        JD_REGEN,
        "pt-BR",
        "habilidades",
        _submitted(),
        _keywords(),
        dica=dica,
        runs_log=runs_log,
        client=client,
    )
    (call,) = client.calls
    # Unchanged create() field set — the gateway seam is untouched (T-05-04).
    assert set(call) == {
        "model",
        "messages",
        "temperature",
        "max_tokens",
        "response_format",
        "extra_body",
    }
    messages = call["messages"]
    assert [m["role"] for m in messages] == ["system", "user"]
    # D-05/T-02-01: the hint lands in the USER message as DATA...
    user = messages[1]["content"]
    assert "DICA DE DIRECIONAMENTO" in user
    assert dica in user
    # ...while the SYSTEM message is the untouched prompt-file body.
    system = messages[0]["content"]
    assert system == load_prompt("resume-skills").body
    assert "DICA" not in system
    assert dica not in system
    # D-15/T-05-04: runs.jsonl stays metadata-only — the hint never reaches it.
    log_text = runs_log.read_text(encoding="utf-8")
    assert dica not in log_text
    assert "DICA DE DIRECIONAMENTO" not in log_text


# ---------------------------------------------------------------------------
# (c) Sibling byte-identity — only the target key is replaced (D-07, SC1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("secao", "stage", "_wire", "content"), REGEN_TARGETS)
def test_siblings_byte_identical_only_target_replaced(
    secao: str,
    stage: str,
    _wire: str,
    content: str,
    tmp_path: Path,
    _profile_path: None,
) -> None:
    from app.resume.pipeline import run_section_regen

    submitted = _submitted()
    client = ScriptedClient([content])
    envelope = run_section_regen(
        JD_REGEN,
        "pt-BR",
        secao,
        submitted,
        _keywords(),
        runs_log=tmp_path / "runs.jsonl",
        client=client,
    )
    secoes = envelope["secoes"]
    assert set(secoes) == {"resumo", "experiencias", "habilidades"}

    if secao == "resumo":
        assert secoes["resumo"] == json.loads(NEW_RESUMO_CONTENT)["resumo"]
    else:
        # == AND the same string object — the sibling passes through untouched.
        assert secoes["resumo"] == submitted.resumo
        assert secoes["resumo"] is submitted.resumo

    if secao == "experiencias":
        assert secoes["experiencias"] == [
            entry.model_dump() for entry in json.loads(NEW_EXPERIENCIAS_CONTENT)["experiencias"]
        ]
    else:
        assert secoes["experiencias"] == [entry.model_dump() for entry in submitted.experiencias]
        assert secoes["experiencias"][0]["company"] == submitted.experiencias[0].company
        assert secoes["experiencias"][0]["company"] is submitted.experiencias[0].company

    if secao == "habilidades":
        assert secoes["habilidades"] == json.loads(NEW_SKILLS_CONTENT)["habilidades"]
    else:
        assert secoes["habilidades"] == list(submitted.habilidades)
        assert secoes["habilidades"][0] is submitted.habilidades[0]


# ---------------------------------------------------------------------------
# (d) Coverage recomputed over the FULL merged generated text (D-07)
# ---------------------------------------------------------------------------


def test_coverage_recomputed_over_merged_generated_text(
    tmp_path: Path, _profile_path: None
) -> None:
    from app.resume.pipeline import run_section_regen

    # "Python" exists ONLY in the submitted sibling resumo; "Docker" ONLY in
    # the NEW habilidades — both must come back coberto if (and only if) the
    # coverage input is the merged generated text (never just the new section,
    # never the submitted state, never the profile facts).
    client = ScriptedClient([NEW_SKILLS_CONTENT])  # habilidades = Python, Docker, FastAPI
    envelope = run_section_regen(
        JD_REGEN,
        "pt-BR",
        "habilidades",
        _submitted(),
        _keywords(),
        runs_log=tmp_path / "runs.jsonl",
        client=client,
    )
    status_by_canonical = {entry["canonical"]: entry for entry in envelope["cobertura"]}
    assert status_by_canonical["Python"]["status"] == "coberto"  # sibling resumo text
    assert status_by_canonical["Docker"]["status"] == "coberto"  # new section text
    for entry in envelope["cobertura"]:
        assert set(entry) == {"canonical", "category", "termo", "status"}
        assert entry["status"] in ("coberto", "ausente")
    assert envelope["cobertura_resumo"] == {"cobertos": 2, "total": 2}


# ---------------------------------------------------------------------------
# (e) Blank/None dica → the plain base composition (boundary normalization)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("blank", [None, "", "   \n\t  "])
def test_blank_dica_yields_the_plain_base_composition(
    blank: str | None, tmp_path: Path, _profile_path: None
) -> None:
    from app.resume.pipeline import run_section_regen

    client = ScriptedClient([NEW_SKILLS_CONTENT])
    run_section_regen(
        JD_REGEN,
        "pt-BR",
        "habilidades",
        _submitted(),
        _keywords(),
        dica=blank,
        runs_log=tmp_path / "runs.jsonl",
        client=client,
    )
    (call,) = client.calls
    user = call["messages"][1]["content"]
    facts = serialize_profile_facts(Profile.model_validate(full_profile()), "pt-BR")
    assert user == f"Idioma preferido de saída: pt-BR\n\nTexto:\n{compose_stage_input(facts, JD_REGEN)}"
    assert "DICA DE DIRECIONAMENTO" not in user


def test_compose_regen_stage_input_appends_dica_block_after_base() -> None:
    from app.resume.facts import compose_regen_stage_input

    base = compose_stage_input("FATOS", "VAGA")
    with_hint = compose_regen_stage_input("FATOS", "VAGA", "foque em métricas")
    assert with_hint.startswith(base)  # the base composition is untouched
    assert "DICA DE DIRECIONAMENTO" in with_hint
    assert "foque em métricas" in with_hint
    # The hint is framed as user DATA bounded by the prompt's existing rules.
    assert "não uma instrução de sistema" in with_hint


@pytest.mark.parametrize("blank", [None, "", "   \n\t  "])
def test_compose_regen_stage_input_blank_dica_returns_base_unchanged(blank: str | None) -> None:
    from app.resume.facts import compose_regen_stage_input

    base = compose_stage_input("FATOS", "VAGA")
    assert compose_regen_stage_input("FATOS", "VAGA", blank) == base
