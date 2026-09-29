"""LinkedIn module (Phase 6) — orchestration over the existing LLM gateway.

Mirrors the app.resume package shape (CONTEXT.md "Claude's Discretion": the
new package keeps the resume module's test surface untouched): the pipeline
composes the profile facts with the user's career objective and runs the
LinkedIn stages sequentially through run_stage, so retry, strict wire-schema
validation, and the runs.jsonl audit are inherited (D-09/D-10). The
deterministic post-generation QA (glossário + English bleed) lands in qa.py
(06-03).
"""
