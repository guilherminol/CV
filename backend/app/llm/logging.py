"""Run-log JSONL writer (D-13/D-14, threat T-02-02).

METADATA ONLY: records carry ts/stage/model/language/attempt/status/tokens/
cost/latency/error — NEVER the API key, full prompts, or response content.
One append per attempt is the atomicity unit: a crash mid-run leaves prior
lines intact. No cross-process locking (personal scale, verification backstop).

Terminal summary (D-13): one `event: "run_summary"` line per run_stage
invocation, emitted on BOTH success and LLMError paths — attempts, status
counts, and token totals are auditable without replaying the attempt lines.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

RUN_SUMMARY_EVENT = "run_summary"


def write_run_line(runs_log: Path, record: dict) -> None:
    """Append ONE UTF-8 JSON line to runs_log.

    Pitfall 5 (Windows): the parent directory is created on first write.
    ensure_ascii=False keeps PT-BR text intact in the file (D-14).
    """
    runs_log.parent.mkdir(parents=True, exist_ok=True)
    with runs_log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_run_summary(runs_log: Path, context: dict, records: list[dict], outcome: str) -> None:
    """Append the terminal run-summary line (D-13).

    `context` supplies stage/model/language/cost from the run's base record;
    `records` are the per-attempt lines already written; `outcome` is the
    run's terminal status: "ok" | "invalid" (exhausted retries) | "error".
    """
    status_counts: dict[str, int] = {}
    for record in records:
        status_counts[record["status"]] = status_counts.get(record["status"], 0) + 1
    summary = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "stage": context["stage"],
        "model": context["model"],
        "language": context["language"],
        "event": RUN_SUMMARY_EVENT,
        "outcome": outcome,
        "attempts": len(records),
        "status_counts": status_counts,
        "prompt_tokens": sum(r["prompt_tokens"] for r in records),
        "completion_tokens": sum(r["completion_tokens"] for r in records),
        "total_tokens": sum(r["total_tokens"] for r in records),
        "cost": context.get("cost"),
        "latency_ms": round(sum(r["latency_ms"] for r in records), 1),
        "error": None if outcome == "ok" else outcome,
    }
    write_run_line(runs_log, summary)
