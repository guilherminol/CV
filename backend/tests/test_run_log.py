"""Run-log contract tests (D-13/D-14) — the runs.jsonl line schema Phases 5/6
parse is pinned HERE, verbatim. Drives the gateway with scripted fake clients
against a tmp_path runs_log; default suite stays offline (D-16).
"""

import json
from pathlib import Path

import pytest

from app.llm.gateway import run_stage

# The pinned attempt-line field contract (D-13 costly — Phase 5/6 run store).
ATTEMPT_LINE_FIELDS = {
    "ts",
    "stage",
    "model",
    "language",
    "attempt",
    "status",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "cost",
    "latency_ms",
    "error",
}

CANNED = json.dumps(
    {
        "keywords": [
            {
                "canonical": "AWS Glue",
                "aliases": [],
                "pt": "AWS Glue",
                "en": "AWS Glue",
                "category": "ferramentas",
            }
        ]
    },
    ensure_ascii=False,
)

INVALID = json.dumps(
    {
        "keywords": [
            {"canonical": "x", "aliases": [], "pt": None, "en": None, "category": "inexistente"}
        ]
    }
)


class _Usage:
    prompt_tokens = 100
    completion_tokens = 50
    total_tokens = 150


class _Resp:
    def __init__(self, content: str):
        self.choices = [type("C", (), {"message": type("M", (), {"content": content})()})()]
        self.usage = _Usage()


class Scripted:
    """Minimal fake chat client: scripted per-attempt contents/exceptions."""

    def __init__(self, script: list):
        self._script = list(script)
        chat = type("Chat", (), {})()
        completions = type("Completions", (), {})()

        def create(**kwargs):
            item = self._script.pop(0)
            if isinstance(item, Exception):
                raise item
            return _Resp(item)

        completions.create = create
        chat.completions = completions
        self.chat = chat


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.llm.gateway.OPENROUTER_API_KEY", "test-key-offline")


def _read_lines(runs_log: Path) -> list[dict]:
    return [json.loads(l) for l in runs_log.read_text(encoding="utf-8").splitlines()]


def _attempt_lines(runs_log: Path) -> list[dict]:
    return [r for r in _read_lines(runs_log) if r.get("event") != "run_summary"]


# ---------------------------------------------------------------------------
# D-14 — retries auditable from the log alone
# ---------------------------------------------------------------------------


def test_three_attempt_run_writes_three_ascending_attempt_lines(tmp_path: Path) -> None:
    """2 invalid + 1 ok → exactly 3 attempt lines, attempts 1,2,3 ascending,
    statuses invalid,invalid,ok (D-14)."""
    runs_log = tmp_path / "runs.jsonl"
    run_stage(
        "keyword-extraction",
        "texto",
        "pt-BR",
        runs_log=runs_log,
        client=Scripted([INVALID, INVALID, CANNED]),
    )
    attempts = _attempt_lines(runs_log)
    assert len(attempts) == 3
    assert [r["attempt"] for r in attempts] == [1, 2, 3]
    assert [r["status"] for r in attempts] == ["invalid", "invalid", "ok"]


def test_every_attempt_line_carries_the_full_field_set(tmp_path: Path) -> None:
    runs_log = tmp_path / "runs.jsonl"
    run_stage("keyword-extraction", "t", "en", runs_log=runs_log, client=Scripted([CANNED]))
    (record,) = _attempt_lines(runs_log)
    assert set(record) == ATTEMPT_LINE_FIELDS  # pinned verbatim (D-13)


def test_ptbr_accents_in_error_field_round_trip(tmp_path: Path) -> None:
    """Pitfall 5: ensure_ascii=False — 'falha de conexão' survives intact."""
    runs_log = tmp_path / "runs.jsonl"
    with pytest.raises(Exception):
        run_stage(
            "keyword-extraction",
            "t",
            "pt-BR",
            runs_log=runs_log,
            client=Scripted([RuntimeError("falha de conexão — timeout")]),
        )
    (record,) = _attempt_lines(runs_log)
    assert "conexão" in record["error"]
    assert "\\u" not in runs_log.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# D-13 — terminal run summary
# ---------------------------------------------------------------------------


def test_terminal_summary_line_is_emitted_and_parses(tmp_path: Path) -> None:
    runs_log = tmp_path / "runs.jsonl"
    run_stage(
        "keyword-extraction",
        "t",
        "pt-BR",
        runs_log=runs_log,
        client=Scripted([INVALID, INVALID, CANNED]),
    )
    lines = _read_lines(runs_log)
    summary = lines[-1]  # last line of the run
    assert summary["event"] == "run_summary"
    assert summary["attempts"] == 3
    assert summary["stage"] == "keyword-extraction"
    assert summary["prompt_tokens"] == 300  # 3 × 100 — totals accumulate
    assert summary["total_tokens"] == 450


def test_summary_emitted_on_llmerror_path_too(tmp_path: Path) -> None:
    from app.llm.errors import LLMError

    runs_log = tmp_path / "runs.jsonl"
    with pytest.raises(LLMError):
        run_stage(
            "keyword-extraction",
            "t",
            "pt-BR",
            runs_log=runs_log,
            client=Scripted([RuntimeError("boom")]),
        )
    summary = _read_lines(runs_log)[-1]
    assert summary["event"] == "run_summary"
    assert summary["outcome"] == "error"


# ---------------------------------------------------------------------------
# Append-only — a crash mid-run never truncates prior lines
# ---------------------------------------------------------------------------


def test_append_never_truncates_preexisting_lines(tmp_path: Path) -> None:
    runs_log = tmp_path / "runs.jsonl"
    runs_log.parent.mkdir(parents=True, exist_ok=True)
    preexisting = {"ts": "2026-01-01T00:00:00Z", "stage": "old-run", "note": "linha antiga"}
    runs_log.write_text(json.dumps(preexisting, ensure_ascii=False) + "\n", encoding="utf-8")

    run_stage("keyword-extraction", "t", "pt-BR", runs_log=runs_log, client=Scripted([CANNED]))
    lines = _read_lines(runs_log)
    assert lines[0] == preexisting  # the pre-existing line survives intact
    assert len(lines) == 3  # pre-existing + 1 attempt + 1 summary
