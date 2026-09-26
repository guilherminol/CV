"""Keyword schema tests — the drift-lock between the hand-maintained strict
JSON Schema dict (wire) and KeywordExtraction's Pydantic model (code).

RESEARCH Pattern 2/Pitfall 1: the wire dict is hand-maintained and NEVER
derived from model_json_schema() at runtime — this test is what keeps the
two representations from diverging silently (threat T-02-08).
"""

import pytest
from pydantic import ValidationError

from app.llm.schemas import KEYWORD_STRICT_SCHEMA, Keyword, KeywordExtraction

# ---------------------------------------------------------------------------
# Drift-lock — wire dict ↔ Pydantic model properties (bidirectional, T-02-08)
# ---------------------------------------------------------------------------


def test_wire_schema_top_level_properties_match_pydantic() -> None:
    pyd = KeywordExtraction.model_json_schema()
    assert set(KEYWORD_STRICT_SCHEMA["properties"]) == set(pyd["properties"])


def test_wire_schema_keyword_item_properties_match_pydantic() -> None:
    pyd_items = KeywordExtraction.model_json_schema()["$defs"]["Keyword"]["properties"]
    wire_items = KEYWORD_STRICT_SCHEMA["properties"]["keywords"]["items"]["properties"]
    assert set(wire_items) == set(pyd_items)  # names match at the nested level too


def test_wire_schema_category_enum_matches_pydantic_literal() -> None:
    pyd_enum = set(
        KeywordExtraction.model_json_schema()["$defs"]["Keyword"]["properties"][
            "category"
        ]["enum"]
    )
    wire_enum = set(
        KEYWORD_STRICT_SCHEMA["properties"]["keywords"]["items"]["properties"][
            "category"
        ]["enum"]
    )
    assert wire_enum == pyd_enum == {
        "competencias",
        "ferramentas",
        "titulos_de_vaga",
        "certificacoes",
    }  # A6: the four pinned ASCII tokens


def _objects(node: dict):
    """Yield every object-typed sub-schema in the wire dict (recursive)."""
    if isinstance(node, dict):
        if node.get("type") == "object" and "properties" in node:
            yield node
        for value in node.values():
            yield from _objects(value)
    elif isinstance(node, list):
        for value in node:
            yield from _objects(value)


def test_strict_shape_every_object_level() -> None:
    # Pattern 2/A2: additionalProperties:false + ALL properties in required
    for obj in _objects(KEYWORD_STRICT_SCHEMA):
        assert obj["additionalProperties"] is False, obj
        assert sorted(obj["required"]) == sorted(obj["properties"]), obj


# ---------------------------------------------------------------------------
# Strict rejection — extra="forbid" + fixed category set (D-06/D-10)
# ---------------------------------------------------------------------------


def test_unknown_category_token_is_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        KeywordExtraction.model_validate(
            {"keywords": [{"canonical": "x", "aliases": [], "pt": None, "en": None, "category": "soft_skills"}]}
        )
    assert "soft_skills" in str(excinfo.value)


def test_unknown_key_is_rejected() -> None:
    with pytest.raises(ValidationError) as excinfo:
        KeywordExtraction.model_validate(
            {
                "keywords": [
                    {
                        "canonical": "x",
                        "aliases": [],
                        "pt": None,
                        "en": None,
                        "category": "competencias",
                        "peso": 10,  # unknown key — extra="forbid"
                    }
                ]
            }
        )
    assert "peso" in str(excinfo.value)


# ---------------------------------------------------------------------------
# Acceptance — canonical-only keywords, proper nouns, translatable pairs (D-09/D-11)
# ---------------------------------------------------------------------------


def test_keyword_canonical_only_with_defaults() -> None:
    kw = Keyword.model_validate({"canonical": "Apache Airflow", "category": "ferramentas"})
    assert kw.aliases == []  # aliases default []
    assert kw.pt is None and kw.en is None  # pt/en optional


def test_proper_noun_with_identical_pt_en_passes() -> None:
    kw = Keyword.model_validate(
        {"canonical": "AWS Glue", "aliases": ["Glue"], "pt": "AWS Glue", "en": "AWS Glue", "category": "ferramentas"}
    )
    assert kw.pt == kw.en == "AWS Glue"  # D-11: proper nouns render identically


def test_translatable_pair_passes() -> None:
    kw = Keyword.model_validate(
        {"canonical": "Pipeline de dados", "aliases": ["data pipeline"], "pt": "Pipeline de dados", "en": "Data pipeline", "category": "competencias"}
    )
    assert kw.en == "Data pipeline"
