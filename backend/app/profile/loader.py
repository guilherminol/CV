"""Fail-fast profile loader.

Every failure mode (missing file, broken YAML, non-UTF-8, schema violation) is
converted to a ProfileError carrying a PT-BR message (UI-rendered, D-13/D-14)
plus the raw technical detail (terminal-only). NO caching of any kind — the
file is re-read and re-validated on every call (D-15).
"""

from pathlib import Path

import frontmatter
import yaml
from pydantic import ValidationError

from app.config import CONTENT_DIR
from app.profile.errors import render_errors_ptbr
from app.profile.models import Profile

PROFILE_PATH = CONTENT_DIR / "profile.md"


class ProfileError(Exception):
    def __init__(self, message_ptbr: str, raw: str):
        super().__init__(message_ptbr)
        self.message_ptbr = message_ptbr
        self.raw = raw  # terminal-only detail (D-13/D-14)


def load_profile(path: Path | None = None) -> Profile:
    """Read + validate content/profile.md. Fresh on every call (D-15).

    The default path resolves at CALL time (not def time) so tests can retarget
    the loader without touching the real content/ directory.
    """
    if path is None:
        path = PROFILE_PATH
    try:
        post = frontmatter.load(str(path), encoding="utf-8")  # Pitfall 7: explicit UTF-8
    except FileNotFoundError:
        raise ProfileError(f"Perfil não encontrado: {path}", f"FileNotFoundError: {path}")
    except yaml.YAMLError as exc:  # verified: yaml.parser.ParserError subclasses YAMLError
        raise ProfileError(
            f"Erro no perfil: {path} — YAML do frontmatter inválido (verifique indentação e dois-pontos)",
            f"{type(exc).__name__}: {exc}",
        )
    except UnicodeDecodeError as exc:
        raise ProfileError(f"Erro no perfil: {path} — arquivo não é UTF-8 válido", repr(exc))

    try:
        # D-05/D-06: ALL content lives in frontmatter; the Markdown body is unused.
        return Profile.model_validate(post.metadata)
    except ValidationError as exc:
        raw = "\n".join(str(e) for e in exc.errors(include_url=False))
        raise ProfileError(render_errors_ptbr(exc, path), raw)
