"""Keyword-extraction output schema (D-09/D-10/D-11).

Conventions (models.py convention — every decision ID documented):
- D-09: each keyword carries canonical form + aliases + pt/en renderings.
- D-11: proper nouns render identically in pt and en (prompt-enforced; the
  schema keeps both fields free-form so this stays a prompt concern).
- D-10: the category set is FIXED — four ASCII tokens (A6); PT-BR display
  labels ("Competências", etc.) live in the prompt/UI, never the schema.
- D-06 (via _Strict, redeclared per PATTERNS §schemas.py): unknown keys fail
  loudly — wire `strict: true` is NOT trusted (threat T-02-03).
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

KeywordCategory = Literal[
    "competencias", "ferramentas", "titulos_de_vaga", "certificacoes"
]


class _Strict(BaseModel):
    """Base for ALL LLM-layer models — unknown keys fail loudly (D-06)."""

    model_config = ConfigDict(extra="forbid")


class Keyword(_Strict):
    canonical: str
    aliases: list[str] = []
    pt: str | None = None
    en: str | None = None
    category: KeywordCategory


class KeywordExtraction(_Strict):
    keywords: list[Keyword]


# --- Resume section stage outputs (Plan 03-01, D-01: one strict schema per
# call). Every field required — no defaults: strict wire mode wants ALL
# properties in `required` anyway, and a missing field in a generated section
# must fail loudly (SC3), never silently default.


class ResumeSummary(_Strict):
    """resumo stage — one run-language summary paragraph."""

    resumo: str


class ExperienciaGerada(_Strict):
    """One generated experience entry — plain run-language strings (D-01)."""

    company: str
    title: str
    bullets: list[str]


class ResumeExperiencias(_Strict):
    """experiencias stage — the generated experience entries."""

    experiencias: list[ExperienciaGerada]


class ResumeSkills(_Strict):
    """skills stage — flat list of the profile's most relevant skills."""

    habilidades: list[str]


# --- LinkedIn stage outputs (Plan 06-01, D-09). CRITICAL (research Pitfall 1
# / D-07): PLAIN str fields — NO max_length anywhere. A length bound here
# makes the gateway retry over-limit output and abort the whole run at
# exhaustion (gateway retry ladder); limits are enforced POST-generation in
# app.linkedin.pipeline (limites.{limite,tamanho,excesso}) + client-side.
# Over-limit output must survive to be surfaced, never rejected (D-07/SC2).


class LinkedinHeadline(_Strict):
    """linkedin-headline stage — one run-language headline line.

    Target ≤ LINKEDIN_HEADLINE_MAX_CHARS is GUIDANCE (prompt-level) — the
    post-generation check owns the bound (D-07); this model deliberately
    accepts any length so over-limit text survives to be flagged.
    """

    headline: str


class LinkedinSobre(_Strict):
    """linkedin-sobre stage — one run-language About text (≤2600 guidance,
    post-gen check owns the bound, D-07)."""

    sobre: str


class ExperienciaLinkedin(_Strict):
    """One generated LinkedIn experience entry — prose paragraphs in
    `descricao` (NOT bullets); company/title are the profile-fact anchors
    (the prompt hard-rules them verbatim from FATOS DO PERFIL)."""

    company: str
    title: str
    descricao: str


class LinkedinExperiencias(_Strict):
    """linkedin-experiencias stage — ONE call returning the per-company
    entries (D-09: localized retry per block, map aligned server-side)."""

    experiencias: list[ExperienciaLinkedin]


class LinkedinSkills(_Strict):
    """linkedin-skills stage — flat list; array order IS the priority order
    (LI-05)."""

    habilidades: list[str]


# Hand-maintained STRICT JSON Schema for KeywordExtraction — sent as
# response_format json_schema to the provider (RESEARCH Pattern 2; PATTERNS
# §schemas.py: never send model_json_schema() raw — Pitfall 1). OpenAI strict
# mode requires additionalProperties: false and ALL properties in `required`
# at every object level; optionals become nullable unions (Pattern 2/A2).
# The drift-lock test (tests/test_keyword_schema.py) fails CI if this dict and
# the Pydantic model diverge (threat T-02-08) — edit BOTH together.
KEYWORD_STRICT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "keywords": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "canonical": {"type": "string"},
                    "aliases": {"type": "array", "items": {"type": "string"}},
                    "pt": {"type": ["string", "null"]},
                    "en": {"type": ["string", "null"]},
                    "category": {
                        "type": "string",
                        "enum": [
                            "competencias",
                            "ferramentas",
                            "titulos_de_vaga",
                            "certificacoes",
                        ],
                    },
                },
                "required": ["canonical", "aliases", "pt", "en", "category"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["keywords"],
    "additionalProperties": False,
}


# Hand-maintained STRICT JSON Schemas for the three resume section stages —
# same rules as KEYWORD_STRICT_SCHEMA (normative comment block above): sent as
# response_format json_schema with strict: true, never derived from
# model_json_schema() at runtime; every property present in `required`,
# additionalProperties: false at EVERY object level. The generalized drift-lock
# harness (tests/test_resume_schema.py) fails CI if any dict and its model
# diverge (threat T-02-08) — edit BOTH together.
RESUME_SUMMARY_STRICT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "resumo": {"type": "string"},
    },
    "required": ["resumo"],
    "additionalProperties": False,
}

RESUME_EXPERIENCIAS_STRICT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "experiencias": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "title": {"type": "string"},
                    "bullets": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["company", "title", "bullets"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["experiencias"],
    "additionalProperties": False,
}

RESUME_SKILLS_STRICT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "habilidades": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["habilidades"],
    "additionalProperties": False,
}


# Hand-maintained STRICT wire schemas for the four LinkedIn stages (plan
# 06-01) — same rules as the resume schemas above (sent as response_format
# json_schema with strict: true, never derived from model_json_schema() at
# runtime; every property in `required`, additionalProperties: false at EVERY
# object level). The drift-lock harness (tests/test_linkedin_schema.py) fails
# CI if any dict and its model diverge (threat T-02-08/T-06-02) — edit BOTH
# together. NOTE (plan 06-01 Task 2): only linkedin-headline is REGISTERED in
# the gateway's _STAGE_SCHEMAS for now — the other three stages land with
# their prompt files in 06-02 (registration without a prompt file would make
# any accidental call fail at the loader; keep the registration surface
# minimal until then).
LINKEDIN_HEADLINE_STRICT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
    },
    "required": ["headline"],
    "additionalProperties": False,
}

LINKEDIN_SOBRE_STRICT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "sobre": {"type": "string"},
    },
    "required": ["sobre"],
    "additionalProperties": False,
}

LINKEDIN_EXPERIENCIAS_STRICT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "experiencias": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "title": {"type": "string"},
                    "descricao": {"type": "string"},
                },
                "required": ["company", "title", "descricao"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["experiencias"],
    "additionalProperties": False,
}

LINKEDIN_SKILLS_STRICT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "habilidades": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["habilidades"],
    "additionalProperties": False,
}

# --- Candidatura application-question stage (vaga → perfil follow-on): one
# strict schema for the single free-text answer block.


class CandidaturaResposta(_Strict):
    """candidatura-resposta stage — one run-language answer paragraph set."""

    resposta: str


CANDIDATURA_RESPOSTA_STRICT_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "resposta": {"type": "string"},
    },
    "required": ["resposta"],
    "additionalProperties": False,
}
