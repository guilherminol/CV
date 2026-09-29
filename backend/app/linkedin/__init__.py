"""LinkedIn module (Phase 6) — orchestration over the existing LLM gateway.

Mirrors the app.resume package shape (CONTEXT.md "Claude's Discretion": the
new package keeps the resume module's test surface untouched): the pipeline
composes the profile facts with the user's career objective and runs the
LinkedIn stages sequentially through run_stage, so retry, strict wire-schema
validation, and the runs.jsonl audit are inherited (D-09/D-10). The
deterministic post-generation QA (glossário + English bleed, D-12..D-14)
ships as pure functions in qa.py and is re-exported here — the public QA
surface of the package.
"""

from app.linkedin.qa import (
    EN_BLEED_TERMS,
    GlossarioSpec,
    ParGlossario,
    apply_glossario,
    detect_english_bleed,
    load_glossario,
    run_linkedin_qa,
)

__all__ = [
    "EN_BLEED_TERMS",
    "GlossarioSpec",
    "ParGlossario",
    "apply_glossario",
    "detect_english_bleed",
    "load_glossario",
    "run_linkedin_qa",
]
