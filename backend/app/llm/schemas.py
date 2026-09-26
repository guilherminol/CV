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


# Hand-maintained minimal STRICT JSON Schema for KeywordExtraction — sent as
# response_format json_schema to the provider (PATTERNS §schemas.py: never send
# model_json_schema() raw; Pitfall 1). OpenAI strict mode requires
# additionalProperties: false and all properties in `required`.
KEYWORD_EXTRACTION_JSON_SCHEMA: dict = {
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
