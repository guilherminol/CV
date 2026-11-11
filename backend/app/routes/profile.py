"""Profile routes — GET /api/profile + POST /api/profile/adicionar.

Both answer the status envelope, never HTTP 500 (D-12/D-13/D-15): a broken
profile or a failed write is a UI-rendered state; the full raw technical
detail goes to the uvicorn terminal log only.
"""

import logging

import frontmatter
import yaml
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Literal

from app.profile import loader
from app.profile.completeness import compute_completude
from app.profile.loader import ProfileError, load_profile
from app.profile.updater import AdicaoKeyword, add_keywords_to_meta
from app.profile.models import Profile

logger = logging.getLogger(__name__)

router = APIRouter()


class AdicaoKeywordIn(BaseModel):
    """One accepted keyword from the vaga panel (KeywordDTO projection)."""

    canonical: str
    pt: str | None = None
    en: str | None = None
    categoria: Literal["competencias", "ferramentas", "certificacoes"]


class AdicionarRequest(BaseModel):
    adicoes: list[AdicaoKeywordIn] = Field(min_length=1)


def _load_meta(path) -> tuple[dict, str]:
    """Raw frontmatter metadata + body — the write path's read half.

    Mirrors loader.py's fail-ladder but returns the DICT (not the model): the
    updater mutates the raw data so the written file keeps the owner's key
    order and body verbatim.
    """
    post = frontmatter.load(str(path), encoding="utf-8")
    return post.metadata, post.content.lstrip("\n")


def _write_meta(path, meta: dict, body: str) -> None:
    """Validate-then-write: an invalid dict can never reach the file."""
    Profile.model_validate(meta)  # raises ValidationError → caller maps to erro envelope
    texto = (
        "---\n"
        + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False, default_flow_style=False)
        + "---\n\n"
        + body
    )
    if not texto.endswith("\n"):
        texto += "\n"
    path.write_text(texto, encoding="utf-8", newline="\n")


@router.get("/api/profile")
def get_profile() -> dict:
    try:
        profile = load_profile()  # fresh load per request — no cache (D-15)
    except ProfileError as exc:
        logger.error("Falha ao carregar perfil:\n%s", exc.raw)  # raw detail → terminal (D-13)
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}
    return {
        "status": "ok",
        "exemplo": profile.example,  # D-11 placeholder flag
        "perfil": profile.model_dump(),
        # D-12: section presence/counts, computed fresh alongside the load
        "completude": compute_completude(profile),
    }


@router.post("/api/profile/adicionar")
def adicionar_ao_perfil(payload: AdicionarRequest) -> dict:
    """Add user-accepted JD keywords to content/profile.md (skills groups or
    name-only certification entries).

    Read → mutate (updater) → validate → write, then answer with the SAME ok
    envelope as GET /api/profile plus the addition report (adicionado /
    ja_existentes — stored names, dedup is casefold-normalized). The ['perfil']
    query invalidates client-side; the next GET re-reads the file fresh (D-15).
    """
    try:
        meta, body = _load_meta(loader.PROFILE_PATH)
    except (ProfileError, OSError, yaml.YAMLError) as exc:
        raw = f"{type(exc).__name__}: {exc}"
        logger.error("Falha ao ler perfil para atualização:\n%s", raw)
        return {"status": "erro", "erros": ["Não foi possível ler o perfil — veja o terminal."]}
    except Exception as exc:  # frontmatter wraps decode errors generically
        raw = f"{type(exc).__name__}: {exc}"
        logger.error("Falha ao ler perfil para atualização:\n%s", raw)
        return {"status": "erro", "erros": ["Não foi possível ler o perfil — veja o terminal."]}

    adicoes = [
        AdicaoKeyword(a.canonical, a.pt, a.en, a.categoria) for a in payload.adicoes
    ]
    adicionado, ja_existentes = add_keywords_to_meta(meta, adicoes)

    if adicionado:
        try:
            _write_meta(loader.PROFILE_PATH, meta, body)
        except Exception as exc:
            raw = f"{type(exc).__name__}: {exc}"
            logger.error("Falha ao gravar perfil:\n%s", raw)
            return {
                "status": "erro",
                "erros": ["Não foi possível gravar o perfil — veja o terminal."],
            }
        logger.info("Perfil atualizado: +%s keyword(s) → %s", len(adicionado), adicionado)

    try:
        profile = load_profile()  # answer from the SAME file the write landed in (D-15)
    except ProfileError as exc:
        logger.error("Falha ao revalidar perfil pós-escrita:\n%s", exc.raw)
        return {"status": "erro", "erros": exc.message_ptbr.splitlines()}

    return {
        "status": "ok",
        "adicionado": adicionado,
        "ja_existentes": ja_existentes,
        "exemplo": profile.example,
        "perfil": profile.model_dump(),
        "completude": compute_completude(profile),
    }

