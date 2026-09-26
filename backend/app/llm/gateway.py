"""LLM gateway — the one path from prompt file to typed, audited output.

load_prompt(stage) fresh (D-08) → compose user message (D-07) → OpenAI SDK
calls against OpenRouter with a strict json_schema response_format →
re-validate with Pydantic (wire `strict: true` is NEVER trusted — T-02-03) →
write ONE runs.jsonl line PER ATTEMPT (D-13/D-14) → return the typed result.

Retry loop (RESEARCH Pattern 3, SC3/D-03/D-04): ValidationError (or invalid
JSON) is retried up to LLM_MAX_ATTEMPTS, ALWAYS appending the assistant's bad
output plus a PT-BR correction request embedding the rendered validation
errors first — identical messages are NEVER resent (Pitfall 7). Exhaustion
raises a loud LLMError; invalid content never returns downstream.

- Model slug from app.config only (D-01/D-02) — never a literal here.
- The client is injectable so the default test suite stays offline (D-16, A3).
- Missing/empty OPENROUTER_API_KEY at CALL time raises LLMError (loud,
  tolerant config notwithstanding).
- Network/API/SDK errors are NOT retried — immediate LLMError, no fallback
  model on any error (D-03).
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from app.config import LLM_MAX_ATTEMPTS, LLM_MODEL, OPENROUTER_API_KEY, RUNS_LOG
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
    messages: list[dict] = [
        {"role": "system", "content": loaded.body},
        {"role": "user", "content": f"Idioma preferido de saída: {language}\n\nTexto:\n{input_text}"},
    ]

    base_record: dict = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "model": LLM_MODEL,
        "language": language,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cost": None,
        "error": None,
    }
    accumulated_raw: list[str] = []

    # Retry loop (Pattern 3): validation errors only; bounded by config (D-04).
    for attempt in range(1, LLM_MAX_ATTEMPTS + 1):
        started = time.perf_counter()
        try:
            resp = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
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
        except Exception as exc:  # SDK/API failure — NOT retried, stay loud (D-03)
            write_run_line(
                runs_log,
                {
                    **base_record,
                    "attempt": attempt,
                    "status": "error",
                    "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                    "error": f"{type(exc).__name__}: {exc}",
                },
            )
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
            raw = f"{type(exc).__name__}: {exc}"
            accumulated_raw.append(f"[tentativa {attempt}] {raw}")
            write_run_line(
                runs_log,
                {
                    **base_record,
                    **_usage_fields(resp),
                    "attempt": attempt,
                    "status": "invalid",
                    "latency_ms": latency_ms,
                    "error": f"{type(exc).__name__} (conteúdo Pydantic-inválido — nunca "
                    f"retornado downstream, SC3)",
                },
            )
            if attempt < LLM_MAX_ATTEMPTS:
                # Pitfall 7: NEVER resend identical messages — append the
                # assistant's bad output, then a PT-BR correction request
                # embedding the rendered validation errors.
                if isinstance(exc, ValidationError):
                    rendered = "\n".join(
                        str(e) for e in exc.errors(include_url=False)
                    )
                    correction = (
                        "A resposta anterior é inválida. Corrija SOMENTE os erros "
                        "abaixo e reenvie o objeto JSON completo:\n" + rendered
                    )
                else:
                    correction = (
                        "A resposta anterior não é JSON válido. Reenvie o objeto "
                        "JSON completo."
                    )
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": correction})
            continue

        write_run_line(
            runs_log,
            {
                **base_record,
                **_usage_fields(resp),
                "attempt": attempt,
                "status": "ok",
                "latency_ms": latency_ms,
            },
        )
        return result

    # Exhaustion (D-03/D-04): loud, PT-BR, raw detail to the terminal only.
    raise LLMError(
        f"Falha na geração após {LLM_MAX_ATTEMPTS} tentativas — resposta "
        f"inválida para o estágio '{stage}' (detalhes no terminal)",
        "\n".join(accumulated_raw),
    )
