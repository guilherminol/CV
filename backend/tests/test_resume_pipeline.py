"""Resume pipeline tests — the three resume stages end-to-end through the
gateway, OFFLINE (D-16): prompt file → gateway → validated section model →
runs.jsonl attempt + run_summary lines carrying the resume stage name.

The SDK client is injected as a fake returning canned content; the default
suite never touches the network. Fakes are copied verbatim from
tests/test_gateway.py (D-16 house pattern).
"""

import json
from pathlib import Path

import pytest

from app.config import LLM_MODEL
from app.llm.errors import LLMError
from app.llm.gateway import run_stage
from app.llm.schemas import ResumeExperiencias, ResumeSkills, ResumeSummary
from app.profile.models import Profile
from app.resume.facts import (
    compose_stage_input,
    resolve_loc,
    serialize_profile_facts,
)
from conftest import full_profile

# ---------------------------------------------------------------------------
# Offline fakes — copied verbatim from tests/test_gateway.py (D-16)
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


class FakeClient:
    """Minimal OpenAI SDK chat-completions surface — records create() kwargs."""

    def __init__(self, content: str):
        self._content = content
        self.calls: list[dict] = []
        chat = type("Chat", (), {})()
        completions = type("Completions", (), {})()

        def create(**kwargs):
            self.calls.append(kwargs)
            return _FakeResponse(self._content)

        completions.create = create
        chat.completions = completions
        self.chat = chat


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


# ---------------------------------------------------------------------------
# Canned content per resume stage (UTF-8 accents survive the JSON round-trip)
# ---------------------------------------------------------------------------

RESUMO_CONTENT = json.dumps(
    {
        "resumo": "Engenheira de dados sênior com pipeline RAG e avaliação automática em produção."
    },
    ensure_ascii=False,
)

EXPERIENCIAS_CONTENT = json.dumps(
    {
        "experiencias": [
            {
                "company": "Exemplo IA",
                "title": "Engenheira de Software Sênior",
                "bullets": [
                    "Implementou um pipeline RAG com avaliação automática, reduzindo o tempo de resposta",
                    "Liderou a adoção de práticas de observabilidade no time de plataforma",
                ],
            },
            {
                "company": "Outra Tech",
                "title": "Engenheira de Dados",
                "bullets": ["Construiu o data lake analítico da companhia"],
            },
        ]
    },
    ensure_ascii=False,
)

SKILLS_CONTENT = json.dumps(
    {"habilidades": ["Python", "FastAPI", "AWS"]},
    ensure_ascii=False,
)

BAD_EXPERIENCIAS_CONTENT = json.dumps(
    {"experiencias": [{"company": "Exemplo IA"}]},  # missing title + bullets
    ensure_ascii=False,
)

STAGES = [
    ("resume-summary", RESUMO_CONTENT, ResumeSummary),
    ("resume-experiencias", EXPERIENCIAS_CONTENT, ResumeExperiencias),
    ("resume-skills", SKILLS_CONTENT, ResumeSkills),
]


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Offline suite: a fake key satisfies the call-time guard (D-16)."""
    monkeypatch.setattr("app.llm.gateway.OPENROUTER_API_KEY", "test-key-offline")


# ---------------------------------------------------------------------------
# (a) Happy path per resume stage, BOTH languages — typed result + runs.jsonl
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("stage", "content", "model_class"), STAGES)
@pytest.mark.parametrize("language", ["pt-BR", "en"])
def test_happy_path_returns_typed_section_and_logs_stage(
    stage: str, content: str, model_class: type, language: str, tmp_path: Path
) -> None:
    runs_log = tmp_path / "logs" / "runs.jsonl"
    fake = FakeClient(content)
    result = run_stage(
        stage,
        "FATOS DO PERFIL\n...\n\nDESCRIÇÃO DA VAGA\nvaga de exemplo",
        language,
        runs_log=runs_log,
        client=fake,
    )
    assert isinstance(result, model_class)
    # PT-BR accents survive the full JSON round-trip (D-14)
    if stage == "resume-summary":
        assert "avaliação automática" in result.resumo
    elif stage == "resume-experiencias":
        assert result.experiencias[0].company == "Exemplo IA"
        assert "avaliação automática" in result.experiencias[0].bullets[0]
        assert len(result.experiencias) == 2
    else:
        assert result.habilidades == ["Python", "FastAPI", "AWS"]

    lines = runs_log.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    # exactly ONE line per attempt + one terminal run_summary (D-13)
    attempt_records = [r for r in records if r.get("event") != "run_summary"]
    assert len(attempt_records) == 1
    summary = records[-1]
    assert summary["event"] == "run_summary"
    assert summary["stage"] == stage  # the terminal line names the resume stage
    assert summary["outcome"] == "ok"
    record = attempt_records[0]
    assert record["stage"] == stage  # the attempt line carries the stage name
    assert record["language"] == language
    assert record["model"] == LLM_MODEL  # slug from config only (D-01/D-02)
    assert record["status"] == "ok"
    # T-02-02: metadata only — no prompt/response content in the log
    assert "avaliação" not in lines[0]
    assert "FATOS DO PERFIL" not in lines[0]


# ---------------------------------------------------------------------------
# (b) Retry loop on a resume stage — invalid-then-valid self-corrects (SC3)
# ---------------------------------------------------------------------------


def test_invalid_then_valid_recovers_on_resume_experiencias(tmp_path: Path) -> None:
    """SC3/D-04 on resume-experiencias: attempt 1 schema-invalid (missing
    title + bullets) → attempt 2 valid. Pitfall 7: the retry appends the
    assistant's bad output + a PT-BR correction embedding the validation
    errors — identical messages are NEVER resent."""
    runs_log = tmp_path / "runs.jsonl"
    fake = ScriptedClient([BAD_EXPERIENCIAS_CONTENT, EXPERIENCIAS_CONTENT])
    result = run_stage(
        "resume-experiencias", "texto", "pt-BR", runs_log=runs_log, client=fake
    )

    assert isinstance(result, ResumeExperiencias)
    assert len(fake.calls) == 2
    retry_messages = fake.calls[1]["messages"]
    assert [m["role"] for m in retry_messages] == ["system", "user", "assistant", "user"]
    assert retry_messages[2]["content"] == BAD_EXPERIENCIAS_CONTENT  # bad output, verbatim
    correction = retry_messages[3]["content"]
    assert "corrija" in correction.lower()  # PT-BR correction request
    assert "bullets" in correction  # rendered validation error embedded

    statuses = [
        json.loads(line)["status"]
        for line in runs_log.read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("event") != "run_summary"
    ]
    assert statuses == ["invalid", "ok"]  # retries auditable from the log (D-14)


# ---------------------------------------------------------------------------
# (c) Unknown stage — loud LLMError listing ALL FOUR available stages
# ---------------------------------------------------------------------------


def test_unknown_stage_error_lists_all_four_stages(tmp_path: Path) -> None:
    with pytest.raises(LLMError) as excinfo:
        run_stage(
            "nao-existe",
            "t",
            "pt-BR",
            runs_log=tmp_path / "runs.jsonl",
            client=FakeClient(RESUMO_CONTENT),
        )
    message = f"{excinfo.value.message_ptbr} {excinfo.value.raw}"
    for stage in (
        "keyword-extraction",
        "resume-summary",
        "resume-experiencias",
        "resume-skills",
    ):
        assert stage in message


# ---------------------------------------------------------------------------
# (d) SDK call shape — each stage carries ITS OWN prompt-file frontmatter
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("stage", "content", "temperature", "max_tokens"),
    [
        ("resume-summary", RESUMO_CONTENT, 0.3, 2000),
        ("resume-experiencias", EXPERIENCIAS_CONTENT, 0.3, 4000),
        ("resume-skills", SKILLS_CONTENT, 0.2, 2000),
    ],
)
def test_sdk_call_shape_carries_stage_frontmatter(
    stage: str,
    content: str,
    temperature: float,
    max_tokens: int,
    tmp_path: Path,
) -> None:
    fake = FakeClient(content)
    run_stage(stage, "MEU-INPUT-DE-TESTE", "en", runs_log=tmp_path / "runs.jsonl", client=fake)
    (kwargs,) = fake.calls
    assert kwargs["model"] == LLM_MODEL
    assert kwargs["temperature"] == temperature  # from that stage's frontmatter (D-04)
    assert kwargs["max_tokens"] == max_tokens
    assert kwargs["response_format"]["json_schema"]["name"] == stage.replace("-", "_")
    assert kwargs["response_format"]["json_schema"]["strict"] is True
    # D-07/T-02-01: the composed input flows through the user message as data
    assert "MEU-INPUT-DE-TESTE" in kwargs["messages"][1]["content"]


# ---------------------------------------------------------------------------
# Profile-fact serialization — the grounding supply line (RESUME-03/D-07)
# ---------------------------------------------------------------------------


def test_resolve_loc_prefers_run_language_then_ptbr_then_first_nonempty() -> None:
    assert resolve_loc({"pt-BR": "pt", "en": "en"}, "en") == "en"
    assert resolve_loc({"pt-BR": "pt"}, "en") == "pt"  # pt-BR fallback
    assert resolve_loc({"en": "", "pt-BR": "pt"}, "en") == "pt"  # empty en skipped
    assert resolve_loc({"en": "only"}, "pt-BR") == "only"  # first non-empty
    assert resolve_loc({"en": "", "pt-BR": ""}, "en") == ""  # nothing non-empty
    assert resolve_loc({}, "en") == ""  # empty map
    assert resolve_loc(None, "en") == ""  # None map


def test_serialize_full_profile_contains_known_profile_strings_ptbr() -> None:
    profile = Profile.model_validate(full_profile())
    blob = serialize_profile_facts(profile, "pt-BR")
    assert "Exemplo IA" in blob  # the company
    assert "-40% no tempo de resposta" in blob  # the profile's own metric
    assert "AWS Certified Solutions Architect" in blob  # the certification
    assert "FATOS" not in blob  # section labels live in compose_stage_input
    assert "Resumo de exemplo." in blob  # pt-BR summary
    assert "Example summary." not in blob  # the other language never leaks


def test_serialize_full_profile_en_renders_en_values() -> None:
    profile = Profile.model_validate(full_profile())
    blob = serialize_profile_facts(profile, "en")
    assert "Example summary." in blob  # en summary
    assert "-40% response time" in blob  # en metric
    assert "Resumo de exemplo." not in blob


def test_serialize_profile_facts_falls_back_to_ptbr_when_en_missing() -> None:
    profile = Profile.model_validate(full_profile())
    profile.summary = {"pt-BR": "Resumo somente em português."}  # drop en
    blob = serialize_profile_facts(profile, "en")
    assert "Resumo somente em português." in blob  # pt-BR fallback (UI-SPEC Zone 4)


def test_serialize_profile_facts_never_contains_absent_tokens() -> None:
    """Grounding probe (D-07): the blob is profile-derived ONLY — a technology
    the profile does not have can never appear in it."""
    profile = Profile.model_validate(full_profile())
    blob = serialize_profile_facts(profile, "pt-BR")
    assert "Snowflake" not in blob


def test_compose_stage_input_contains_facts_and_jd_verbatim() -> None:
    facts = "DADOS DE CONTATO:\nNOME: Ana Exemplo\nEMAIL: ana.exemplo@example.com"
    jd = "Vaga: engenheiro de dados com experiência em Snowflake"
    blob = compose_stage_input(facts, jd)
    assert "FATOS DO PERFIL" in blob  # the facts section label
    assert "DESCRIÇÃO DA VAGA" in blob  # the JD section label
    assert facts in blob  # facts verbatim
    assert jd in blob  # pasted JD verbatim (data, never instruction — T-02-01)


# ---------------------------------------------------------------------------
# (e) Orchestration — run_lint_only + run_resume_pipeline (plan 03-03):
# 4 scripted stages through the REAL pipeline functions, offline via the
# injected client; PROFILE_PATH retargeted to the conftest fixture (D-15 seam).
# ---------------------------------------------------------------------------

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
            {
                "canonical": "Engenheiro de Dados",
                "aliases": ["Data Engineer"],
                "pt": "Engenheiro de Dados",
                "en": "Data Engineer",
                "category": "titulos_de_vaga",
            },
            {
                "canonical": "AWS Certified Solutions Architect",
                "aliases": [],
                "pt": "AWS Certified Solutions Architect",
                "en": "AWS Certified Solutions Architect",
                "category": "certificacoes",
            },
        ]
    },
    ensure_ascii=False,
)

# Script order = pipeline call order: extraction, then D-01 section order.
PIPELINE_SCRIPT = [KEYWORDS_CONTENT, RESUMO_CONTENT, EXPERIENCIAS_CONTENT, SKILLS_CONTENT]


@pytest.fixture
def _profile_path(monkeypatch: pytest.MonkeyPatch, valid_profile_path: Path) -> None:
    """Loader seam: load_profile() re-resolves PROFILE_PATH at call time (D-15)."""
    monkeypatch.setattr("app.profile.loader.PROFILE_PATH", valid_profile_path)


@pytest.mark.parametrize("language", ["pt-BR", "en"])
def test_run_resume_pipeline_returns_contract_envelope(
    language: str, tmp_path: Path, _profile_path: None
) -> None:
    from app.resume.pipeline import run_resume_pipeline

    client = ScriptedClient(list(PIPELINE_SCRIPT))
    envelope = run_resume_pipeline(
        "Vaga de exemplo com Python e Docker",
        language,
        runs_log=tmp_path / "runs.jsonl",
        client=client,
    )

    # Exact ok-envelope key set of the normative contract — nothing more.
    assert set(envelope) == {
        "status",
        "idioma",
        "keywords",
        "avisos",
        "secoes",
        "cobertura",
        "cobertura_resumo",
    }
    assert envelope["status"] == "ok"
    assert envelope["idioma"] == language
    # Keywords echoed VERBATIM from this call's own extraction stage.
    assert envelope["keywords"] == json.loads(KEYWORDS_CONTENT)["keywords"]
    # Full profile fixture → no D-04 gaps: lint is non-blocking but empty here.
    assert envelope["avisos"] == []

    # D-01: extraction, then the three section stages SEQUENTIALLY in order.
    stage_names = [
        call["response_format"]["json_schema"]["name"] for call in client.calls
    ]
    assert stage_names == [
        "keyword_extraction",
        "resume_summary",
        "resume_experiencias",
        "resume_skills",
    ]

    # secoes shapes — exactly the 3 generated sections.
    secoes = envelope["secoes"]
    assert set(secoes) == {"resumo", "experiencias", "habilidades"}
    assert secoes["resumo"] == json.loads(RESUMO_CONTENT)["resumo"]
    assert secoes["experiencias"] == json.loads(EXPERIENCIAS_CONTENT)["experiencias"]
    assert secoes["habilidades"] == json.loads(SKILLS_CONTENT)["habilidades"]

    # Coverage runs over the GENERATED text only; exact integer tally.
    cobertura = envelope["cobertura"]
    assert len(cobertura) == len(envelope["keywords"])
    resumo_cov = envelope["cobertura_resumo"]
    assert set(resumo_cov) == {"cobertos", "total"}  # no score anywhere
    assert resumo_cov["total"] == len(cobertura)
    assert 0 <= resumo_cov["cobertos"] <= resumo_cov["total"]

    status_by_canonical = {entry["canonical"]: entry for entry in cobertura}
    # "Python" appears in the generated habilidades → coberto in both languages.
    assert status_by_canonical["Python"]["status"] == "coberto"
    assert status_by_canonical["Python"]["termo"] == "Python"
    # Docker exists ONLY in the profile facts (skills inventory), never in the
    # canned generated text — the generated-text-only input is pinned here
    # (Pitfall 7): a profile-passthrough input would flip this to coberto.
    profile_blob = serialize_profile_facts(
        Profile.model_validate(full_profile()), language
    )
    assert "Docker" in profile_blob  # it IS a profile fact…
    assert status_by_canonical["Docker"]["status"] == "ausente"  # …and stays ausente
    assert status_by_canonical["Docker"]["termo"] is None


def test_run_lint_only_returns_keywords_verbatim_and_avisos(
    tmp_path: Path, _profile_path: None
) -> None:
    from app.resume.pipeline import run_lint_only

    result = run_lint_only(
        "Vaga de exemplo com Python e Docker",
        runs_log=tmp_path / "runs.jsonl",
        client=FakeClient(KEYWORDS_CONTENT),
    )
    assert set(result) == {"keywords", "avisos"}
    assert result["keywords"] == json.loads(KEYWORDS_CONTENT)["keywords"]
    assert result["avisos"] == []


def test_run_lint_only_loads_profile_before_the_paid_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """IN-04 (review fix): load_profile() runs BEFORE the paid extraction
    stage — a broken profile fails /lint without consuming an OpenRouter
    call (the same load-first order run_resume_pipeline pins)."""
    from app.profile.loader import ProfileError
    from app.resume import pipeline

    order: list[str] = []

    def broken_profile() -> None:
        order.append("load_profile")
        raise ProfileError("perfil quebrado (IN-04)", "raw: perfil quebrado (IN-04)")

    monkeypatch.setattr(pipeline, "load_profile", broken_profile)
    client = FakeClient(KEYWORDS_CONTENT)

    with pytest.raises(ProfileError):
        pipeline.run_lint_only(
            "Vaga de exemplo com Python e Docker",
            runs_log=tmp_path / "runs.jsonl",
            client=client,
        )

    # The loader failed FIRST and the extraction stage never ran — zero paid
    # calls consumed (an empty client.calls proves run_stage never fired).
    assert order == ["load_profile"]
    assert client.calls == []


def test_run_resume_pipeline_raises_llm_error_on_scripted_failure(
    tmp_path: Path, _profile_path: None
) -> None:
    """All-or-nothing (T-03-07): a stage failure propagates OUT of the
    pipeline untouched — no swallowing, no partial envelope construction."""
    from app.resume.pipeline import run_resume_pipeline

    client = ScriptedClient([RuntimeError("boom-na-extração")])
    with pytest.raises(LLMError):
        run_resume_pipeline(
            "Vaga de exemplo",
            "pt-BR",
            runs_log=tmp_path / "runs.jsonl",
            client=client,
        )
    assert client.calls[-1]["response_format"]["json_schema"]["name"] == (
        "keyword_extraction"
    )  # the failure happened at the FIRST stage — nothing ran after it
