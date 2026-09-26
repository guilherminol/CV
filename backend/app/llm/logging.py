"""Run-log JSONL writer (D-13/D-14, threat T-02-02).

METADATA ONLY: records carry ts/stage/model/language/attempt/status/tokens/
cost/latency/error — NEVER the API key, full prompts, or response content.
One append per attempt is the atomicity unit: a crash mid-run leaves prior
lines intact. No cross-process locking (personal scale, verification backstop).
"""

import json
from pathlib import Path


def write_run_line(runs_log: Path, record: dict) -> None:
    """Append ONE UTF-8 JSON line to runs_log.

    Pitfall 5 (Windows): the parent directory is created on first write.
    ensure_ascii=False keeps PT-BR text intact in the file (D-14).
    """
    runs_log.parent.mkdir(parents=True, exist_ok=True)
    with runs_log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
