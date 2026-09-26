"""Gateway tracer tests — the FULL path, OFFLINE (D-16): prompt file →
gateway → validated KeywordExtraction → one runs.jsonl line.

The SDK client is injected as a fake returning canned content; the default
suite never touches the network (A3).
"""

import json
from pathlib import Path

import pytest

from app.config import LLM_MODEL
from app.llm.errors import LLMError
from app.llm.gateway import run_stage
from app.llm.logging import write_run_line
from app.llm.schemas import KeywordExtraction

CANNED_CONTENT = json.dumps(
    {
        "keywords": [
            {
                "canonical": "AWS Glue",
                "aliases": ["Glue"],
                "pt": "AWS Glue",
                "en": "AWS Glue",
                "category": "ferramentas",
            },
            {
                "canonical": "Pipeline de dados",
                "aliases": ["data pipeline"],
                "pt": "Pipeline de dados",
                "en": "Data pipeline",
                "category": "competencias",
            },
            {
                "canonical": "Arquitetura de dados",
                "aliases": [],
                "pt": "Arquitetura de dados",
                "en": "Data architecture",
                "category": "competencias",
            },
        ]
    },
    ensure_ascii=False,
)


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


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Offline suite: a fake key satisfies the call-time guard (D-16) — the
    missing-key test overrides this with an explicit empty value."""
    monkeypatch.setattr("app.llm.gateway.OPENROUTER_API_KEY", "test-key-offline")


# ---------------------------------------------------------------------------
# Happy path — full offline tracer through every layer
# ---------------------------------------------------------------------------


def test_happy_path_returns_typed_extraction_and_logs_one_line(tmp_path: Path) -> None:
    runs_log = tmp_path / "logs" / "runs.jsonl"
    fake = FakeClient(CANNED_CONTENT)
    result = run_stage(
        "keyword-extraction",
        "Vaga: engenheiro de dados com AWS Glue, pipeline de dados e arquitetura de dados.",
        "pt-BR",
        runs_log=runs_log,
        client=fake,
    )
    assert isinstance(result, KeywordExtraction)
    assert [k.canonical for k in result.keywords] == [
        "AWS Glue",
        "Pipeline de dados",
        "Arquitetura de dados",
    ]
    # PT-BR accents survive the full JSON round-trip (D-14)
    assert result.keywords[1].pt == "Pipeline de dados"
    assert result.keywords[2].en == "Data architecture"

    lines = runs_log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1  # exactly ONE line per attempt (D-14)
    record = json.loads(lines[0])
    assert record["stage"] == "keyword-extraction"
    assert record["model"] == LLM_MODEL  # slug from config only (D-01/D-02)
    assert record["language"] == "pt-BR"
    assert record["attempt"] == 1
    assert record["status"] == "ok"
    assert record["prompt_tokens"] == 120
    assert record["completion_tokens"] == 80
    assert record["total_tokens"] == 200
    assert isinstance(record["latency_ms"], (int, float))
    assert record["ts"]
    # T-02-02: metadata only — no prompt or response content in the log
    assert "AWS Glue" not in lines[0]
    assert "Vaga" not in lines[0]


def test_sdk_call_shape_strict_schema_and_extra_body(tmp_path: Path) -> None:
    fake = FakeClient(CANNED_CONTENT)
    run_stage(
        "keyword-extraction", "texto", "en", runs_log=tmp_path / "runs.jsonl", client=fake
    )
    (kwargs,) = fake.calls
    assert kwargs["model"] == LLM_MODEL
    assert kwargs["temperature"] == 0.2  # from the real prompt file (D-04)
    assert kwargs["max_tokens"] == 2000
    assert kwargs["response_format"]["type"] == "json_schema"
    assert kwargs["response_format"]["json_schema"]["strict"] is True
    # Pitfall 2: require_parameters rides in the BODY, never a header
    assert kwargs["extra_body"] == {"provider": {"require_parameters": True}}
    # D-07/T-02-01: prompt-file body is the system message; input is user data
    assert kwargs["messages"][0]["role"] == "system"
    assert "palavras-chave" in kwargs["messages"][0]["content"]
    assert kwargs["messages"][1]["role"] == "user"
    assert "texto" in kwargs["messages"][1]["content"]


# ---------------------------------------------------------------------------
# Failure containment — loud, logged, never downstream (D-03/SC3)
# ---------------------------------------------------------------------------


def test_invalid_content_raises_llmerror_logs_invalid_and_never_returns(tmp_path: Path) -> None:
    bad = json.dumps({"keywords": [{"canonical": "x", "category": "inexistente"}]})
    runs_log = tmp_path / "runs.jsonl"
    with pytest.raises(LLMError) as excinfo:
        run_stage("keyword-extraction", "t", "pt-BR", runs_log=runs_log, client=FakeClient(bad))
    assert excinfo.value.message_ptbr
    assert excinfo.value.raw
    record = json.loads(runs_log.read_text(encoding="utf-8").splitlines()[0])
    assert record["status"] == "invalid"
    assert record["error"]


def test_missing_key_raises_llmerror_at_call_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.llm.gateway.OPENROUTER_API_KEY", "")
    with pytest.raises(LLMError) as excinfo:
        run_stage("keyword-extraction", "t", "pt-BR", client=FakeClient(CANNED_CONTENT))
    assert "OPENROUTER_API_KEY" in excinfo.value.message_ptbr
    assert not (tmp_path / "runs.jsonl").exists()  # failed before any call/log


def test_unknown_stage_raises_llmerror() -> None:
    with pytest.raises(LLMError):
        run_stage("nao-existe", "t", "pt-BR", client=FakeClient(CANNED_CONTENT))


# ---------------------------------------------------------------------------
# write_run_line — UTF-8 discipline (Pitfall 5/7, D-14)
# ---------------------------------------------------------------------------


def test_write_run_line_creates_dir_and_keeps_accents(tmp_path: Path) -> None:
    runs_log = tmp_path / "novo-dir" / "runs.jsonl"
    write_run_line(runs_log, {"status": "ok", "error": "correção"})
    raw = runs_log.read_text(encoding="utf-8")
    assert "correção" in raw  # ensure_ascii=False — no \u00e7 escapes
    assert "\\u" not in raw
    write_run_line(runs_log, {"status": "ok"})  # second attempt appends
    assert len(runs_log.read_text(encoding="utf-8").splitlines()) == 2
