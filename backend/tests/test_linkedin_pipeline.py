"""LinkedIn pipeline tests — run_linkedin_pipeline + compose_linkedin_stage_input
(plan 06-01 tracer, LI-01/D-07/D-10/D-15), OFFLINE.

Pinned here, via a ScriptedClient recording every create() kwargs (copied
verbatim from tests/test_resume_regen_pipeline.py's D-16 house pattern) and a
retargeted PROFILE_PATH (D-15 seam):

- (a) happy path: the envelope carries EXACTLY {idioma, secoes, limites}; the
  headline stage's wire schema name is linkedin_headline with strict: true;
  the user message is the FATOS DO PERFIL + OBJETIVO DE CARREIRA composition
  (T-06-01: objetivo as DATA) and the system message is the untouched
  prompt-file body;
- (b) runs.jsonl contract intact (D-10): a real scripted run appends exactly
  the "linkedin-headline" stage string — and stays metadata-only (the
  generated headline text NEVER reaches the log);
- (c) empty/blank generated headline → LLMError LOUD (probe edge LI-02/empty)
  — an empty block is never returned for rendering;
- (d) over-limit generated headline → envelope ok with excesso > 0 and the
  FULL text intact — nothing truncated, nothing rejected (D-07);
- (e) code-unit counting (probe edge LI-02/encoding): tamanho == Python len
  of the exact returned string, including accented multi-byte characters.
"""

import json
from pathlib import Path

import pytest

from app.llm.errors import LLMError
from app.llm.gateway import load_prompt

# ---------------------------------------------------------------------------
# Offline fakes — copied verbatim from tests/test_resume_regen_pipeline.py
# (the D-16 house pattern; test_resume_pipeline.py origin)
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

OBJETIVO = (
    "Crescer como engenheiro de dados sênior com foco em Python, SQL e "
    "plataformas de dados em nuvem, liderando iniciativas de dados que "
    "impactem o negócio."
)

HEADLINE_CONTENT = json.dumps(
    {"headline": "Engenheira de Dados Sênior — Python, SQL e plataformas de dados em nuvem"},
    ensure_ascii=False,
)

OVERLIMIT_HEADLINE = "Headline sênior de dados com Python e SQL " + "x" * 300
OVERLIMIT_HEADLINE_CONTENT = json.dumps({"headline": OVERLIMIT_HEADLINE}, ensure_ascii=False)


@pytest.fixture
def _profile_path(monkeypatch: pytest.MonkeyPatch, valid_profile_path: Path) -> None:
    """Loader seam: load_profile() re-resolves PROFILE_PATH at call time (D-15)."""
    monkeypatch.setattr("app.profile.loader.PROFILE_PATH", valid_profile_path)


# ---------------------------------------------------------------------------
# (a) Happy path — envelope shape + gateway seam untouched (T-06-01)
# ---------------------------------------------------------------------------


def test_run_linkedin_pipeline_happy_path_envelope(
    tmp_path: Path, _profile_path: None
) -> None:
    from app.linkedin.pipeline import run_linkedin_pipeline

    client = ScriptedClient([HEADLINE_CONTENT])
    envelope = run_linkedin_pipeline(
        OBJETIVO, "pt-BR", runs_log=tmp_path / "runs.jsonl", client=client
    )
    assert len(client.calls) == 1  # tracer: exactly the headline stage
    call = client.calls[0]
    # Unchanged create() field set — the gateway seam is untouched.
    assert set(call) == {
        "model",
        "messages",
        "temperature",
        "max_tokens",
        "response_format",
        "extra_body",
    }
    wire = call["response_format"]["json_schema"]
    assert wire["name"] == "linkedin_headline"  # stage.replace("-", "_")
    assert wire["strict"] is True
    messages = call["messages"]
    assert [m["role"] for m in messages] == ["system", "user"]
    # The SYSTEM message is the untouched prompt-file body (T-02-01/T-06-01).
    assert messages[0]["content"] == load_prompt("linkedin-headline").body
    # The objetivo lands in the USER message as DATA inside the composition.
    user = messages[1]["content"]
    assert "FATOS DO PERFIL:" in user
    assert "OBJETIVO DE CARREIRA:" in user
    assert OBJETIVO in user

    # The normative tracer envelope: exactly these keys, nothing more.
    assert set(envelope) == {"idioma", "secoes", "limites"}
    assert envelope["idioma"] == "pt-BR"
    assert set(envelope["secoes"]) == {"headline"}
    assert envelope["secoes"]["headline"] == json.loads(HEADLINE_CONTENT)["headline"]
    limites = envelope["limites"]["headline"]
    assert set(limites) == {"limite", "tamanho", "excesso"}
    assert limites["limite"] == 220
    headline = envelope["secoes"]["headline"]
    assert limites["tamanho"] == len(headline)
    assert limites["excesso"] == 0  # within the limit — nothing flagged


def test_run_linkedin_pipeline_language_en_passes_through(
    tmp_path: Path, _profile_path: None
) -> None:
    from app.linkedin.pipeline import run_linkedin_pipeline

    client = ScriptedClient([HEADLINE_CONTENT])
    envelope = run_linkedin_pipeline(
        OBJETIVO, "en", runs_log=tmp_path / "runs.jsonl", client=client
    )
    assert envelope["idioma"] == "en"
    user = client.calls[0]["messages"][1]["content"]
    assert "Idioma preferido de saída: en" in user


# ---------------------------------------------------------------------------
# (b) runs.jsonl contract intact — stage string + metadata-only (D-10)
# ---------------------------------------------------------------------------


def test_runs_log_gains_exactly_the_linkedin_headline_stage(
    tmp_path: Path, _profile_path: None
) -> None:
    from app.linkedin.pipeline import run_linkedin_pipeline

    runs_log = tmp_path / "runs.jsonl"
    client = ScriptedClient([HEADLINE_CONTENT])
    run_linkedin_pipeline(OBJETIVO, "pt-BR", runs_log=runs_log, client=client)

    lines = [json.loads(line) for line in runs_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines, "runs.jsonl must gain at least one line"
    attempt_stages = {
        record["stage"] for record in lines if record.get("event") != "run_summary"
    }
    assert attempt_stages == {"linkedin-headline"}  # D-10: stage as a plain string
    # Metadata-only (D-10/D-13): the generated headline text NEVER reaches the log.
    log_text = runs_log.read_text(encoding="utf-8")
    assert json.loads(HEADLINE_CONTENT)["headline"] not in log_text


# ---------------------------------------------------------------------------
# (c) Empty/blank headline → LLMError LOUD (probe edge LI-02/empty)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("blank", ["", "   \n\t  "])
def test_empty_headline_fails_loud(
    blank: str, tmp_path: Path, _profile_path: None
) -> None:
    from app.linkedin.pipeline import run_linkedin_pipeline

    client = ScriptedClient([json.dumps({"headline": blank}, ensure_ascii=False)])
    with pytest.raises(LLMError) as excinfo:
        run_linkedin_pipeline(OBJETIVO, "pt-BR", runs_log=tmp_path / "runs.jsonl", client=client)
    assert "headline vazio" in excinfo.value.message_ptbr
    # Raw detail carries the mechanical descriptor (terminal-only path).
    assert "empty headline content" in excinfo.value.raw


# ---------------------------------------------------------------------------
# (d) Over-limit headline → flagged, NEVER truncated (D-07)
# ---------------------------------------------------------------------------


def test_overlimit_headline_survives_flagged_not_truncated(
    tmp_path: Path, _profile_path: None
) -> None:
    from app.linkedin.pipeline import run_linkedin_pipeline

    client = ScriptedClient([OVERLIMIT_HEADLINE_CONTENT])
    envelope = run_linkedin_pipeline(
        OBJETIVO, "pt-BR", runs_log=tmp_path / "runs.jsonl", client=client
    )
    headline = envelope["secoes"]["headline"]
    assert headline == OVERLIMIT_HEADLINE  # the FULL text — nothing cut
    limites = envelope["limites"]["headline"]
    assert len(headline) > limites["limite"]
    assert limites["excesso"] == len(headline) - limites["limite"]
    assert limites["excesso"] > 0


# ---------------------------------------------------------------------------
# (e) Code-unit counting (probe edge LI-02/encoding)
# ---------------------------------------------------------------------------


def test_counter_is_code_unit_count_on_accented_text(
    tmp_path: Path, _profile_path: None
) -> None:
    from app.linkedin.pipeline import run_linkedin_pipeline

    accented = "Engenharia de Dados — Ação, Coração, Pé e Aço " + "á" * 180
    content = json.dumps({"headline": accented}, ensure_ascii=False)
    client = ScriptedClient([content])
    envelope = run_linkedin_pipeline(
        OBJETIVO, "pt-BR", runs_log=tmp_path / "runs.jsonl", client=client
    )
    limites = envelope["limites"]["headline"]
    # len() on the SAME string that comes back — multi-byte chars count once.
    assert limites["tamanho"] == len(accented)
    assert envelope["secoes"]["headline"] == accented


# ---------------------------------------------------------------------------
# compose_linkedin_stage_input — the Pattern-2 composition (T-06-01)
# ---------------------------------------------------------------------------


def test_compose_linkedin_stage_input_shape() -> None:
    from app.linkedin.pipeline import compose_linkedin_stage_input

    composed = compose_linkedin_stage_input("FATOS", "OBJETIVO")
    assert composed == "FATOS DO PERFIL:\nFATOS\n\nOBJETIVO DE CARREIRA:\nOBJETIVO"
