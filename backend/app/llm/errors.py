"""LLM-layer errors (D-03, D-13/D-14).

Exact ProfileError shape (app/profile/loader.py:22-27): a PT-BR message for
the UI path plus raw technical detail for the terminal only. Pydantic
ValidationError rendering reuses app.profile.errors.render_errors_ptbr —
the same Pydantic error types (extra_forbidden, missing, string_type,
list_type, literal_error) recur for prompt frontmatter and LLM responses,
so the PT-BR map carries over unchanged.
"""

from pathlib import Path

from pydantic import ValidationError

from app.profile.errors import _ptbr_message, render_loc, render_errors_ptbr  # noqa: F401

__all__ = [
    "PromptError",
    "LLMError",
    "render_errors_ptbr",
    "render_prompt_errors_ptbr",
]


def render_prompt_errors_ptbr(exc: ValidationError, path: Path) -> str:
    """Same D-14 bullet-line rendering as render_errors_ptbr, with the
    prompt-file header ("Erro no prompt: {path}") instead of the profile one."""
    lines = [f"Erro no prompt: {path}"]
    for e in exc.errors(include_url=False):
        lines.append(f"  • {render_loc(e['loc'])} — {_ptbr_message(e)}")
    return "\n".join(lines)


class PromptError(Exception):
    """Prompt-file failure (missing, bad YAML, non-UTF-8, schema violation)."""

    def __init__(self, message_ptbr: str, raw: str):
        super().__init__(message_ptbr)
        self.message_ptbr = message_ptbr
        self.raw = raw  # terminal-only detail (D-13/D-14)


class LLMError(Exception):
    """LLM call failure (missing key, API error, exhausted retries) — D-03:
    never silently falls back to another model; always loud."""

    def __init__(self, message_ptbr: str, raw: str):
        super().__init__(message_ptbr)
        self.message_ptbr = message_ptbr
        self.raw = raw  # terminal-only detail (D-13/D-14)
