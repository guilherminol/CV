"""Fail-fast meta-prompt loader (D-05..D-08).

Mirrors app/profile/loader.py's try/except ladder exactly: every failure mode
(missing file, broken YAML, non-UTF-8, schema violation) becomes a PromptError
carrying a PT-BR message (UI path, D-13/D-14) plus raw technical detail
(terminal only). NO caching — the file is re-read and re-validated on every
call (D-08/SC1): edit a prompt file and the next run_stage call sees the edit.

Difference from the profile loader: the Markdown body IS the payload (the
system prompt, D-07) — load_prompt returns both the validated frontmatter
(PromptSpec) and the body.
"""

from dataclasses import dataclass
from pathlib import Path

import frontmatter
import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from app.config import PROMPTS_DIR
from app.llm.errors import PromptError, render_prompt_errors_ptbr


class _Strict(BaseModel):
    """Unknown frontmatter keys fail loudly (D-06) — same discipline as D-10."""

    model_config = ConfigDict(extra="forbid")


class PromptSpec(_Strict):
    """Strict prompt-file frontmatter (D-06): id + generation parameters."""

    id: str
    temperature: float
    max_tokens: int


@dataclass(frozen=True)
class LoadedPrompt:
    """Validated frontmatter + the raw Markdown body (the system prompt, D-07)."""

    spec: PromptSpec
    body: str


def load_prompt(stage: str, prompts_dir: Path | None = None) -> LoadedPrompt:
    """Read + validate prompts/<stage>.md. Fresh on every call (D-08/SC1).

    The default directory resolves at CALL time (not def time) so tests can
    retarget the loader with tmp_path without touching the real prompts/ dir.
    """
    if prompts_dir is None:
        prompts_dir = PROMPTS_DIR
    path = prompts_dir / f"{stage}.md"
    try:
        post = frontmatter.load(str(path), encoding="utf-8")  # Pitfall 7: explicit UTF-8
    except FileNotFoundError:
        raise PromptError(f"Prompt não encontrado: {path}", f"FileNotFoundError: {path}")
    except yaml.YAMLError as exc:
        raise PromptError(
            f"Erro no prompt: {path} — YAML do frontmatter inválido (verifique indentação e dois-pontos)",
            f"{type(exc).__name__}: {exc}",
        )
    except UnicodeDecodeError as exc:
        raise PromptError(f"Erro no prompt: {path} — arquivo não é UTF-8 válido", repr(exc))

    try:
        # Frontmatter = generation parameters; body = system prompt (D-07).
        spec = PromptSpec.model_validate(post.metadata)
    except ValidationError as exc:
        raw = "\n".join(str(e) for e in exc.errors(include_url=False))
        raise PromptError(render_prompt_errors_ptbr(exc, path), raw)
    return LoadedPrompt(spec=spec, body=post.content)
