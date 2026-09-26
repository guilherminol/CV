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
