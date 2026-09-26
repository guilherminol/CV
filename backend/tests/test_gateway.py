"""Gateway tracer tests — the FULL path, OFFLINE (D-16): prompt file →
gateway → validated KeywordExtraction → one runs.jsonl line.

The SDK client is injected as a fake returning canned content; the default
suite never touches the network (A3).
"""

import json
from pathlib import Path

import pytest

from app.config import LLM_MAX_ATTEMPTS, LLM_MODEL
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


class ScriptedClient:
    """Fake returning a scripted SEQUENCE of contents, prebuilt response
    objects (anything with a `.choices` attribute — returned verbatim, never
    wrapped), or raising scripted exceptions — one per attempt — recording
    every create() call."""

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
            if hasattr(item, "choices"):  # prebuilt response object — verbatim
                return item
            return _FakeResponse(item)

        completions.create = create
        chat.completions = completions
        self.chat = chat


BAD_CATEGORY_CONTENT = json.dumps(
    {
        "keywords": [
            {"canonical": "x", "aliases": [], "pt": None, "en": None, "category": "inexistente"}
        ]
    }
)


def _shape_response(content: object = None, *, empty_choices: bool = False) -> object:
    """Malformed-but-200 response (CR-01): either an EMPTY choices list
    (provider error surfaced inside HTTP 200) or a single choice whose
    message.content is None / a non-str (refusal / content-block list).
    Plain type(...) namespace pattern like the other fakes; _FakeUsage stays
    attached so the containment line still carries usage metadata."""
    choices = [] if empty_choices else [
        type("Choice", (), {"message": type("Msg", (), {"content": content})()})()
    ]
    return type("Resp", (), {"choices": choices, "usage": _FakeUsage(), "cost": None})()


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
    records = [json.loads(l) for l in lines]
    # exactly ONE line per attempt + one terminal summary (D-13/D-14)
    attempt_records = [r for r in records if r.get("event") != "run_summary"]
    assert len(attempt_records) == 1
    summary = records[-1]
    assert summary["event"] == "run_summary"
    assert summary["outcome"] == "ok"
    record = attempt_records[0]
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


# ---------------------------------------------------------------------------
# Retry loop — validation errors self-correct or fail loud (SC3, D-03/D-04)
# ---------------------------------------------------------------------------


def test_invalid_then_valid_recovers_with_appended_correction(tmp_path: Path) -> None:
    """SC3/D-04: attempt 1 invalid (unknown category) → attempt 2 valid.
    Pitfall 7: the retry NEVER resends identical messages — the assistant's
    bad output + a PT-BR correction request embedding the validation error
    are appended first."""
    runs_log = tmp_path / "runs.jsonl"
    fake = ScriptedClient([BAD_CATEGORY_CONTENT, CANNED_CONTENT])
    result = run_stage("keyword-extraction", "texto", "pt-BR", runs_log=runs_log, client=fake)

    assert isinstance(result, KeywordExtraction)
    assert len(fake.calls) == 2
    retry_messages = fake.calls[1]["messages"]
    assert [m["role"] for m in retry_messages] == ["system", "user", "assistant", "user"]
    assert retry_messages[2]["content"] == BAD_CATEGORY_CONTENT  # the bad output, verbatim
    correction = retry_messages[3]["content"]
    assert "corrija" in correction.lower()  # PT-BR correction request
    assert "inexistente" in correction  # the rendered validation error is embedded

    statuses = [
        json.loads(l)["status"]
        for l in runs_log.read_text(encoding="utf-8").splitlines()
        if json.loads(l).get("event") != "run_summary"
    ]
    assert statuses == ["invalid", "ok"]  # retries auditable from the log alone (D-14)


def test_exhausted_retries_raise_llmerror_after_max_attempts(tmp_path: Path) -> None:
    """D-04/D-03: always-invalid → LLMError after exactly LLM_MAX_ATTEMPTS."""
    runs_log = tmp_path / "runs.jsonl"
    fake = ScriptedClient([BAD_CATEGORY_CONTENT] * (LLM_MAX_ATTEMPTS + 2))
    with pytest.raises(LLMError) as excinfo:
        run_stage("keyword-extraction", "t", "pt-BR", runs_log=runs_log, client=fake)
    assert len(fake.calls) == LLM_MAX_ATTEMPTS  # bounded by config (D-04)
    assert "tentativas" in excinfo.value.message_ptbr
    assert "inexistente" in excinfo.value.raw  # accumulated validation detail

    records = [
        json.loads(l)
        for l in runs_log.read_text(encoding="utf-8").splitlines()
        if json.loads(l).get("event") != "run_summary"
    ]
    assert [r["status"] for r in records] == ["invalid"] * LLM_MAX_ATTEMPTS
    assert [r["attempt"] for r in records] == list(range(1, LLM_MAX_ATTEMPTS + 1))


def test_api_error_is_fatal_immediate_no_retry(tmp_path: Path) -> None:
    """D-03: network/API errors are NOT retried — LLMError on attempt 1."""
    runs_log = tmp_path / "runs.jsonl"
    fake = ScriptedClient([RuntimeError("connection reset by peer")])
    with pytest.raises(LLMError) as excinfo:
        run_stage("keyword-extraction", "t", "pt-BR", runs_log=runs_log, client=fake)
    assert len(fake.calls) == 1  # exactly one attempt — no retry, no fallback
    assert "connection reset" in excinfo.value.raw
    record = json.loads(runs_log.read_text(encoding="utf-8").splitlines()[0])
    assert record["status"] == "error"
    assert record["attempt"] == 1


# ---------------------------------------------------------------------------
# Malformed-but-200 response shapes — SAME containment path (CR-01/SC3)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("response", "type_name"),
    [
        pytest.param(_shape_response(empty_choices=True), "NoneType", id="empty-choices"),
        pytest.param(_shape_response(None), "NoneType", id="content-none"),
        pytest.param(_shape_response(["bloco"]), "list", id="content-non-str"),
    ],
)
def test_malformed_response_shapes_contained_like_invalid_content(
    response: object, type_name: str, tmp_path: Path
) -> None:
    """CR-01/SC3: a malformed-but-200 shape (empty choices / content=None /
    non-str content) routes through the SAME containment path as invalid
    content — invalid attempt lines + terminal run_summary in runs.jsonl,
    bounded retry, loud LLMError at exhaustion. A raw IndexError/TypeError
    never escapes run_stage."""
    runs_log = tmp_path / "runs.jsonl"
    fake = ScriptedClient([response] * (LLM_MAX_ATTEMPTS + 2))
    with pytest.raises(LLMError) as excinfo:
        run_stage(
            "keyword-extraction",
            "TEXTO-SECRETO-DO-USUARIO",
            "pt-BR",
            runs_log=runs_log,
            client=fake,
        )
    assert len(fake.calls) == LLM_MAX_ATTEMPTS  # bounded by config (D-04)
    assert "tentativas" in excinfo.value.message_ptbr
    assert "malformed response" in excinfo.value.raw  # descriptor, not content

    records = [
        json.loads(line)
        for line in runs_log.read_text(encoding="utf-8").splitlines()
    ]
    attempts = [r for r in records if r.get("event") != "run_summary"]
    assert len(attempts) == LLM_MAX_ATTEMPTS
    assert [r["status"] for r in attempts] == ["invalid"] * LLM_MAX_ATTEMPTS
    assert [r["attempt"] for r in attempts] == list(range(1, LLM_MAX_ATTEMPTS + 1))
    for r in attempts:
        assert "conteúdo ausente ou não-textual" in r["error"]
        assert type_name in r["error"]  # shape descriptor only — never the value
    summary = records[-1]
    assert summary["event"] == "run_summary"
    assert summary["outcome"] == "invalid"

    # T-02-05-02: metadata-only on the new path — no input text, no payload
    raw_log = runs_log.read_text(encoding="utf-8")
    assert "TEXTO-SECRETO-DO-USUARIO" not in raw_log
    assert "bloco" not in raw_log


def test_malformed_shape_then_valid_recovers_with_correction(tmp_path: Path) -> None:
    """SC3/D-04 on the malformed-shape path: attempt 1 empty choices →
    attempt 2 valid. The retry appends ONLY a user correction (no assistant
    turn — nothing valid to echo back), so roles are ["system", "user",
    "user"] — deliberately different from the validation-path recovery."""
    runs_log = tmp_path / "runs.jsonl"
    fake = ScriptedClient([_shape_response(empty_choices=True), CANNED_CONTENT])
    result = run_stage("keyword-extraction", "texto", "pt-BR", runs_log=runs_log, client=fake)

    assert isinstance(result, KeywordExtraction)
    assert len(fake.calls) == 2
    retry_messages = fake.calls[1]["messages"]
    assert [m["role"] for m in retry_messages] == ["system", "user", "user"]
    assert "Reenvie o objeto JSON completo" in retry_messages[-1]["content"]

    records = [
        json.loads(line)
        for line in runs_log.read_text(encoding="utf-8").splitlines()
    ]
    attempts = [r for r in records if r.get("event") != "run_summary"]
    assert [r["status"] for r in attempts] == ["invalid", "ok"]
    summary = records[-1]
    assert summary["event"] == "run_summary"
    assert summary["outcome"] == "ok"
    assert summary["attempts"] == 2


def test_prompt_file_edit_is_visible_on_next_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SC1/D-08 at gateway level: editing the prompt file between calls
    changes what the next call sends — fresh read, no cache."""
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    prompt_path = prompts_dir / "keyword-extraction.md"

    def _write_prompt(body: str) -> None:
        prompt_path.write_text(
            f"---\nid: keyword-extraction\ntemperature: 0.2\nmax_tokens: 100\n---\n\n{body}",
            encoding="utf-8",
        )

    _write_prompt("VERSAO-UM do system prompt")
    monkeypatch.setattr("app.llm.prompts.PROMPTS_DIR", prompts_dir)
    first = FakeClient(CANNED_CONTENT)
    run_stage("keyword-extraction", "t", "pt-BR", runs_log=tmp_path / "runs.jsonl", client=first)

    _write_prompt("VERSAO-DOIS do system prompt")  # edit between calls, no code change
    second = FakeClient(CANNED_CONTENT)
    run_stage("keyword-extraction", "t", "pt-BR", runs_log=tmp_path / "runs.jsonl", client=second)

    assert "VERSAO-UM" in first.calls[0]["messages"][0]["content"]
    assert "VERSAO-DOIS" in second.calls[0]["messages"][0]["content"]


def test_missing_key_raises_before_any_client_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.llm.gateway.OPENROUTER_API_KEY", "")
    fake = FakeClient(CANNED_CONTENT)
    with pytest.raises(LLMError):
        run_stage("keyword-extraction", "t", "pt-BR", runs_log=tmp_path / "runs.jsonl", client=fake)
    assert fake.calls == []  # the client was never contacted
