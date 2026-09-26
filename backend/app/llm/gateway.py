"""LLM gateway — the one path from prompt file to typed, audited output.

Happy path only in this tracer (retry loop lands in Plan 02-03):
load_prompt(stage) fresh (D-08) → compose user message (D-07) → OpenAI SDK
call against OpenRouter with a strict json_schema response_format →
re-validate with Pydantic (wire `strict: true` is NEVER trusted — T-02-03) →
write ONE runs.jsonl line (D-13/D-14) → return the typed result.

- Model slug from app.config only (D-01/D-02) — never a literal here.
- The client is injectable so the default test suite stays offline (D-16, A3).
- Missing/empty OPENROUTER_API_KEY at CALL time raises LLMError (loud,
  tolerant config notwithstanding).
- No silent model fallback on any error (D-03).
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from app.config import LLM_MODEL, OPENROUTER_API_KEY, RUNS_LOG
from app.llm.errors import LLMError
from app.llm.logging import write_run_line
from app.llm.prompts import load_prompt
from app.llm.schemas import KEYWORD_STRICT_SCHEMA, KeywordExtraction

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# stage → output schema + its strict wire JSON Schema. Full drift-lock
# machinery is Plan 02-03; a single-entry map is enough for the tracer.
_STAGE_SCHEMAS: dict[str, tuple[type, dict]] = {
    "keyword-extraction": (KeywordExtraction, KEYWORD_STRICT_SCHEMA),
}


def _usage_fields(resp: object) -> dict:
    """Metadata-only usage fields from the SDK response (automatic — no
    include param needed). Absent usage (fake clients, error shapes) → zeros."""
    usage = getattr(resp, "usage", None)
    if usage is None:
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
        "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
        "total_tokens": getattr(usage, "total_tokens", 0) or 0,
    }


def run_stage(
    stage: str,
    input_text: str,
    language: str,
    runs_log: Path | None = None,
    client: object | None = None,
) -> KeywordExtraction:
    """Run one generation stage end-to-end. See module docstring.

    `client` is an OpenAI SDK-compatible chat client (injectable for offline
    tests — D-16). `runs_log` defaults to config.RUNS_LOG at CALL time.
    """
    if stage not in _STAGE_SCHEMAS:
        raise LLMError(
            f"Estágio de geração desconhecido: '{stage}' (disponíveis: "
            f"{', '.join(sorted(_STAGE_SCHEMAS))})",
            f"unknown stage: {stage}",
        )
    output_model, wire_schema = _STAGE_SCHEMAS[stage]
    if runs_log is None:
        runs_log = RUNS_LOG
    if not OPENROUTER_API_KEY:  # fail loud at call time (D-03)
        raise LLMError(
            "OPENROUTER_API_KEY ausente — configure a chave no arquivo .env "
            "antes de gerar textos",
            "OPENROUTER_API_KEY empty or missing at call time",
        )
    if client is None:
        from openai import OpenAI  # deferred: tests never import-dial the SDK path

        client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)

    loaded = load_prompt(stage)  # fresh read every call (D-08/SC1)
    # D-07: the prompt-file body is the SYSTEM message; runtime inputs are the
    # USER message (T-02-01: pasted text is data, never instruction).
    user_message = f"Idioma preferido de saída: {language}\n\nTexto:\n{input_text}"

    started = time.perf_counter()
    base_record: dict = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "model": LLM_MODEL,
        "language": language,
        "attempt": 1,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cost": None,
        "error": None,
    }
    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": loaded.body},
                {"role": "user", "content": user_message},
            ],
            temperature=loaded.spec.temperature,
            max_tokens=loaded.spec.max_tokens,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": stage.replace("-", "_"),
                    "strict": True,
                    "schema": wire_schema,
                },
            },
            extra_body={"provider": {"require_parameters": True}},  # Pitfall 2: body, not header
        )
    except Exception as exc:  # SDK/API failure — log metadata, stay loud (D-03)
        record = {
            **base_record,
            "status": "error",
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "error": f"{type(exc).__name__}: {exc}",
        }
        write_run_line(runs_log, record)
        raise LLMError(
            f"Falha na chamada ao modelo ({stage}): {type(exc).__name__}",
            f"{type(exc).__name__}: {exc}",
        ) from exc

    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    content = resp.choices[0].message.content
    try:
        parsed = json.loads(content)
        result = output_model.model_validate(parsed)  # SC3/T-02-03: never trust the wire
    except (json.JSONDecodeError, ValidationError) as exc:
        record = {
            **base_record,
            **_usage_fields(resp),
            "status": "invalid",
            "latency_ms": latency_ms,
            "error": f"{type(exc).__name__} (conteúdo Pydantic-inválido — nunca "
            f"retornado downstream, SC3)",
        }
        write_run_line(runs_log, record)
        raw = f"{type(exc).__name__}: {exc}"
        raise LLMError(
            f"Resposta do modelo inválida para o estágio '{stage}' — o conteúdo "
            f"não passa na validação e não será usado",
            raw,
        ) from exc

    write_run_line(
        runs_log,
        {
            **base_record,
            **_usage_fields(resp),
            "status": "ok",
            "latency_ms": latency_ms,
        },
    )
    return result
