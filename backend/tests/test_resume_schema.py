"""Resume section schema tests — the generalized drift-lock harness over ALL
FOUR hand-maintained strict wire schemas (keyword + the 3 resume stages) and
the strict-model behavior of the new section models (Plan 03-01 Task 1).

RESEARCH Pattern 2/Pitfall 1: each wire dict is hand-maintained and NEVER
derived from model_json_schema() at runtime — these tests keep every wire
dict and its Pydantic model from diverging silently (threat T-02-08,
inherited from tests/test_keyword_schema.py).

Planned symbols resolve LAZILY inside the tests (#3770): a RED run must fail
on assertions about the planned behavior, never on a collection-time
ImportError (that would be INVALID_RED).
"""

import pytest
from pydantic import ValidationError

import app.llm.schemas as schemas
from app.llm.schemas import KEYWORD_STRICT_SCHEMA

# The four wire schemas under drift-lock: (wire-dict attr, model attr).
WIRES_AND_MODELS = [
    ("KEYWORD_STRICT_SCHEMA", "KeywordExtraction"),
    ("RESUME_SUMMARY_STRICT_SCHEMA", "ResumeSummary"),
    ("RESUME_EXPERIENCIAS_STRICT_SCHEMA", "ResumeExperiencias"),
    ("RESUME_SKILLS_STRICT_SCHEMA", "ResumeSkills"),
]


def _sym(name: str):
    """Resolve a planned schema symbol at test time — a missing symbol is a
    FAILED assertion about planned behavior, not a collection crash."""
    if not hasattr(schemas, name):
        pytest.fail(f"planned symbol missing from app.llm.schemas: {name}")
    return getattr(schemas, name)


# ---------------------------------------------------------------------------
# Drift-lock — wire dict ↔ Pydantic model (bidirectional, T-02-08, generalized)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "ResumeSummary",
        "ExperienciaGerada",
        "ResumeExperiencias",
        "ResumeSkills",
        "RESUME_SUMMARY_STRICT_SCHEMA",
        "RESUME_EXPERIENCIAS_STRICT_SCHEMA",
        "RESUME_SKILLS_STRICT_SCHEMA",
    ],
)
def test_planned_symbols_exist(name: str) -> None:
    assert hasattr(schemas, name), f"app.llm.schemas must define {name}"


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


def test_strict_shape_every_object_level_all_four_wire_schemas() -> None:
    # Pattern 2/A2: additionalProperties:false + ALL properties in required,
    # at EVERY object level of all FOUR hand-maintained wire dicts.
    for wire_name, _ in WIRES_AND_MODELS:
        wire = _sym(wire_name)
        for obj in _objects(wire):
            assert obj["additionalProperties"] is False, (wire_name, obj)
            assert sorted(obj["required"]) == sorted(obj["properties"]), (wire_name, obj)


def test_wire_schema_top_level_properties_match_pydantic_all_four() -> None:
    for wire_name, model_name in WIRES_AND_MODELS:
        wire = _sym(wire_name)
        model = _sym(model_name)
        assert set(wire["properties"]) == set(model.model_json_schema()["properties"]), (
            wire_name,
            model_name,
        )


def test_resume_experiencias_nested_item_properties_match_pydantic() -> None:
    wire = _sym("RESUME_EXPERIENCIAS_STRICT_SCHEMA")
    ExperienciaGerada = _sym("ExperienciaGerada")
    wire_items = wire["properties"]["experiencias"]["items"]["properties"]
    pyd_items = ExperienciaGerada.model_json_schema()["properties"]
    assert set(wire_items) == set(pyd_items)  # names match at the nested level too


# ---------------------------------------------------------------------------
# Strict-model behavior — extra="forbid" everywhere (D-06 via _Strict)
# ---------------------------------------------------------------------------


def test_resume_summary_accepts_valid_payload() -> None:
    ResumeSummary = _sym("ResumeSummary")
    parsed = ResumeSummary.model_validate({"resumo": "Texto do resumo"})
    assert parsed.resumo == "Texto do resumo"


def test_resume_summary_rejects_undeclared_key() -> None:
    ResumeSummary = _sym("ResumeSummary")
    with pytest.raises(ValidationError) as excinfo:
        ResumeSummary.model_validate({"resumo": "x", "extra": 1})
    assert "extra" in str(excinfo.value)  # extra="forbid" — unknown keys fail loudly


def test_experiencia_gerada_accepts_valid_entry() -> None:
    ExperienciaGerada = _sym("ExperienciaGerada")
    parsed = ExperienciaGerada.model_validate(
        {"company": "Exemplo IA", "title": "Engenheira", "bullets": ["b1"]}
    )
    assert parsed.company == "Exemplo IA"
    assert parsed.title == "Engenheira"
    assert parsed.bullets == ["b1"]


def test_resume_experiencias_accepts_full_payload() -> None:
    ResumeExperiencias = _sym("ResumeExperiencias")
    parsed = ResumeExperiencias.model_validate(
        {
            "experiencias": [
                {"company": "Exemplo IA", "title": "Engenheira", "bullets": ["b1", "b2"]}
            ]
        }
    )
    assert parsed.experiencias[0].company == "Exemplo IA"
    assert parsed.experiencias[0].bullets == ["b1", "b2"]


def test_resume_experiencias_missing_bullets_is_rejected() -> None:
    ResumeExperiencias = _sym("ResumeExperiencias")
    with pytest.raises(ValidationError):
        ResumeExperiencias.model_validate(
            {"experiencias": [{"company": "Exemplo IA", "title": "Engenheira"}]}
        )


def test_resume_skills_accepts_list() -> None:
    ResumeSkills = _sym("ResumeSkills")
    parsed = ResumeSkills.model_validate({"habilidades": ["Python", "FastAPI"]})
    assert parsed.habilidades == ["Python", "FastAPI"]
