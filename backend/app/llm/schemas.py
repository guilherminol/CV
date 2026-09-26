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
