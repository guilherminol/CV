# Phase 2 — OpenRouter API Coverage Matrix

External API: **OpenRouter** (`https://openrouter.ai/api/v1`), accessed via the `openai` PyPI SDK (OpenAI-compatible endpoint). Verified against official docs 2026-09-25 (see 02-RESEARCH.md Sources).

| Capability | Status | Reason |
|------------|--------|--------|
| Chat completions (POST /chat/completions, non-streaming) | INTEGRATE | The single call path every LLM request flows through (gateway). |
| Structured outputs (`response_format: {type: json_schema, strict: true}`) | INTEGRATE | Core of schema-validated generation (SC3); Pydantic re-validation layered on top because per-provider enforcement varies. |
| Provider preferences (`extra_body.provider.require_parameters`) | INTEGRATE | Routes only to providers honoring response_format — prevents silent JSON-in-prose (Pitfall 2). Body field, NOT a header. |
| Usage / cost reporting (`resp.usage` incl. `.cost` in credits) | INTEGRATE | Automatic in non-streaming responses; `cost` feeds every `logs/runs.jsonl` line (D-13). No `usage: {include: true}` needed (deprecated). |
| Error / status surface (400/401/404/429/5xx) | INTEGRATE | Fail-loud handling (D-03): no fallback, clear PT-BR error + raw detail in terminal/log. |
| Model listing (GET /models) | OPT-OUT | Single global slug lives in config (D-01/D-02); the `-m llm` slug-probe test validates the pinned slug directly against chat completions — a listing endpoint adds nothing. |
| Streaming (SSE) | OPT-OUT | Non-personal-scale feature; responses are small structured JSON, streaming adds complexity with zero benefit at personal scale. |
| Response Healing | OPT-OUT (passive) | Occurs server-side when enabled by provider routing; we do not configure it — Pydantic re-validation + retry loop (D-04) is our explicit, auditable correction mechanism. |
| Abuse monitoring / generation endpoints | OPT-OUT | Not applicable to a personal localhost tool with no user-generated public content. |
