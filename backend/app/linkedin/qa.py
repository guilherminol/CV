"""Deterministic post-generation QA for LinkedIn output (SC4, D-12..D-14).

Pure functions + ONE file read — no LLM client anywhere in this module (D-14:
no LLM judge; detection is mechanical or nothing), no network, offline-
testable by construction. The pipeline (plan 06-02) calls run_linkedin_qa on
EVERY generation success (full run or section regen) over the PT-BR merged
state, so the report always describes the CURRENT artifact.

Input discipline: run_linkedin_qa receives the secoes DICT shape the pipeline
builds/merges ({"headline": str, "sobre": str, "experiencias": [entries],
"habilidades": [str]}). The glossary substitution MUTATES the prose surfaces
in place — the user copies the POST-glossary text, so the displayed text and
the report can never disagree (D-13 + research constraint #4). Habilidades
entries are NEVER rewritten (substituting inside a skill name would silently
alter the deliverable list) — they get bleed detection only.

Non-blocking contract (D-14): QA findings are payload rows, never failures.
Nothing in this module raises for findings — the ONLY loud path is the
glossário load, where a malformed user-edited file raises PromptError through
the same fail-fast ladder as every prompt file (hard failures stay reserved
for schema/network errors; D-14). Language gate: QA is defined for PT-BR
outputs only (SC4) — an "en" run returns None and the frontend renders the
neutral note (never a silently absent verdict).

Mechanics (research Patterns 3-5):
- The glossário is a git-versioned Markdown+YAML file (prompts/glossario.md,
  D-12) validated STRICTLY (extra=forbid) and re-read FRESH on every call —
  edit-and-next-run, no caching.
- Substitution matches case-insensitively on the ORIGINAL text with
  lookaround boundaries and re.escape — never on a folded copy (folding
  breaks offsets; Pitfall 3), never \\b (the C++/C#/.NET lesson). Replacement
  preserves the match's case shape; each applied pair is reported with its
  occurrence count (D-13 auditability, T-06-12).
- Bleed detection reuses the coverage matcher primitives by import — one
  matcher, many inputs (fold + lookarounds, matching ONLY: no rewrite happens
  here, so offsets are irrelevant) — over a curated static term list OWNED IN
  CODE (D-14).
"""

import re
from pathlib import Path

import frontmatter
import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.config import PROMPTS_DIR
from app.llm.errors import PromptError, render_prompt_errors_ptbr
from app.resume.coverage import _fold, _term_pattern

GLOSSARIO_STAGE = "glossario"


class _Strict(BaseModel):
    """Unknown frontmatter keys fail loudly — same discipline as PromptSpec."""

    model_config = ConfigDict(extra="forbid")


class ParGlossario(_Strict):
    """One de→para pair. Empty strings are malformed (an empty `de` would
    substitute at every word boundary, corrupting the whole text; an empty
    `para` would silently DELETE the term) — min_length=1 keeps a malformed
    pair from ever reaching the substitution engine (T-06-10)."""

    de: str = Field(min_length=1)
    para: str = Field(min_length=1)


class GlossarioSpec(_Strict):
    """Strict glossário frontmatter (D-12): id + the pair list."""

    id: str
    pares: list[ParGlossario]


def load_glossario(prompts_dir: Path | None = None) -> GlossarioSpec:
    """Read + validate prompts/glossario.md. Fresh on every call (D-12).

    The load_prompt fail-fast ladder verbatim (app/llm/prompts.py): every
    failure mode becomes a PromptError carrying a PT-BR message (UI path)
    plus raw technical detail (terminal only). The default directory resolves
    at CALL time (not def time) so tests can retarget the loader with tmp_path
    without touching the real prompts/ dir. Validation errors reuse the
    shared render_prompt_errors_ptbr — its header names the offending file.
    """
    if prompts_dir is None:
        prompts_dir = PROMPTS_DIR
    path = prompts_dir / f"{GLOSSARIO_STAGE}.md"
    try:
        post = frontmatter.load(str(path), encoding="utf-8")  # explicit UTF-8
    except FileNotFoundError:
        raise PromptError(
            f"Glossário não encontrado: {path}", f"FileNotFoundError: {path}"
        )
    except yaml.YAMLError as exc:
        raise PromptError(
            f"Erro no glossário: {path} — YAML do frontmatter inválido (verifique indentação e dois-pontos)",
            f"{type(exc).__name__}: {exc}",
        )
    except UnicodeDecodeError as exc:
        raise PromptError(f"Erro no glossário: {path} — arquivo não é UTF-8 válido", repr(exc))

    try:
        spec = GlossarioSpec.model_validate(post.metadata)
    except ValidationError as exc:
        raw = "\n".join(str(e) for e in exc.errors(include_url=False))
        raise PromptError(render_prompt_errors_ptbr(exc, path), raw)
    return spec


def _apply_pair(text: str, de: str, para: str) -> tuple[str, int]:
    """Replace case-insensitive whole-term matches of `de` with `para`,
    preserving the match's case shape. Returns (new_text, substitution_count).

    Matching happens on the ORIGINAL text (re.IGNORECASE + lookarounds over
    the raw string) — NEVER on a folded copy, whose offsets would corrupt the
    reconstruction (Pitfall 3). Boundaries are lookarounds only — \\b is
    forbidden project-wide (C++/C#/.NET false-negative lesson).
    """
    pattern = re.compile(r"(?<!\w)" + re.escape(de) + r"(?!\w)", re.IGNORECASE)

    def _casematch(m: re.Match) -> str:
        found = m.group(0)
        if found.isupper() and len(found) > 1:
            return para.upper()
        if found[0].isupper():
            return para[0].upper() + para[1:]
        return para

    return pattern.subn(_casematch, text)


def apply_glossario(text: str, spec: GlossarioSpec) -> tuple[str, list[dict]]:
    """Apply every glossary pair to `text` (D-13): mechanical, case-preserving
    substitutions over the original string; each pair with count > 0 yields a
    report row {"de", "para", "ocorrencias"} — substitutions are auditable,
    never silent (T-06-12). A zero-match pair yields no row and leaves the
    text unchanged. Pairs apply in file order, each over the result of the
    previous one."""
    texto = text
    relatorio: list[dict] = []
    for par in spec.pares:
        texto, ocorrencias = _apply_pair(texto, par.de, par.para)
        if ocorrencias > 0:
            relatorio.append({"de": par.de, "para": par.para, "ocorrencias": ocorrencias})
    return texto, relatorio


# The English-bleed heuristic term list (D-14): curated, static, OWNED IN
# CODE. Multi-word constructions and EN action verbs/first-person forms come
# first — their presence mid-sentence in PT-BR prose signals an untranslated
# stretch. Short high-frequency tokens ship ONLY where no standalone PT-BR
# word collides under fold+lookaround matching (the negative controls in
# test_linkedin_qa.py pin this); "for" was deliberately DROPPED because it is
# a real PT-BR verb ("se for necessário", "quando for preciso") and would
# false-positive on every such sentence. Consolidated tech proper nouns
# (Python, Kubernetes, machine learning…) are deliberately EXCLUDED — they
# are legitimate in PT-BR tech writing; the QA legend concedes the residual
# false positives either way. Non-blocking by construction (D-14): findings
# render as amber avisos and never gate Copiar.
EN_BLEED_TERMS: tuple[str, ...] = (
    # Multi-word EN constructions (lowest false-positive risk in PT-BR)
    "responsible for",
    "strong background",
    "team player",
    "track record",
    "my experience",
    # EN first-person constructions
    "i am",
    "i have",
    # EN resume action verbs — an EN verb in PT-BR text = untranslated sentence
    "managed",
    "led",
    "achieved",
    "spearheaded",
    "drove",
    "delivered",
    # Short EN function words with NO standalone PT-BR collision ("for" is
    # excluded — see the list comment above)
    "and",
    "with",
    "from",
)


def detect_english_bleed(text: str, secao: str) -> list[dict]:
    """Mechanical EN-bleed detection over `text` (D-14): fold + lookaround
    matching of every EN_BLEED_TERMS entry — the coverage matcher primitives
    by import (one matcher, many inputs), never a re-implementation, never
    \\b. Folding is for MATCHING only; no rewrite happens here, so offsets
    are irrelevant. Returns {"termo", "secao"} rows in list order — `secao`
    labels where the term was found (the frontend renders the row verbatim
    as `{termo} — {seção}`; D-13 discipline: no frontend re-mapping)."""
    folded = _fold(text)
    return [
        {"termo": termo, "secao": secao}
        for termo in EN_BLEED_TERMS
        if _term_pattern(termo).search(folded)
    ]


def run_linkedin_qa(
    secoes: dict, language: str, prompts_dir: Path | None = None
) -> dict | None:
    """The orchestration seam (SC4): glossary FIRST, then bleed detection on
    the POST-glossary text (research constraint #4 — the report describes
    exactly the text the user copies).

    For "pt-BR": applies the glossário to the prose surfaces (headline,
    sobre, each experiência descricao — MUTATED in place, see the module
    docstring), then runs bleed detection over the post-glossary text of
    those surfaces plus every habilidades entry (detected ONLY — never
    rewritten). Returns {"glossario": [rows], "bleed": [rows]} — possibly
    with empty lists, which the frontend renders as loud zero lines. For
    "en": returns None (QA is defined for PT-BR outputs; SC4) — the language
    gate short-circuits BEFORE the glossário read, so an EN run never touches
    the file. `prompts_dir` threads the load_glossario test seam through.
    """
    if language != "pt-BR":
        return None

    spec = load_glossario(prompts_dir)

    relatorio: list[dict] = []
    for superficie in ("headline", "sobre"):
        texto, rows = apply_glossario(secoes[superficie], spec)
        secoes[superficie] = texto
        relatorio.extend(rows)
    for entry in secoes["experiencias"]:
        texto, rows = apply_glossario(entry["descricao"], spec)
        entry["descricao"] = texto
        relatorio.extend(rows)

    # Bleed over the POST-glossary text only — the report and the copied
    # text must agree (research constraint #4). Experiência rows are labeled
    # by the entry's company (the fixed profile-fact anchor the frontend
    # renders as the sub-block header); habilidade rows carry the skill
    # itself, the exact deliverable line where the term sits.
    bleed: list[dict] = []
    for superficie in ("headline", "sobre"):
        bleed.extend(detect_english_bleed(secoes[superficie], superficie))
    for entry in secoes["experiencias"]:
        bleed.extend(detect_english_bleed(entry["descricao"], entry["company"]))
    for habilidade in secoes["habilidades"]:
        bleed.extend(detect_english_bleed(habilidade, habilidade))

    return {"glossario": relatorio, "bleed": bleed}
