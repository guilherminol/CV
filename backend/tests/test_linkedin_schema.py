"""LinkedIn schema tests — the drift-lock harness over the hand-maintained
strict wire schema for linkedin-headline and the strict-model behavior of
LinkedinHeadline (plan 06-01; mirrors tests/test_resume_schema.py).

RESEARCH Pitfall 1 / D-07: the wire dict is hand-maintained and NEVER derived
from model_json_schema() at runtime; the LinkedIn output models carry PLAIN
str fields — no per-field length bounds anywhere (a bound would make the
gateway retry over-limit output and abort the run). These tests keep the wire
dict and its Pydantic model from diverging silently (threat T-02-08/T-06-02)
and pin the no-length-bound contract with an oversize vector.

Planned symbols resolve LAZILY inside the tests (#3770): a RED run must fail
on assertions about the planned behavior, never on a collection-time
ImportError (that would be INVALID_RED).
"""

import pytest
from pydantic import ValidationError

import app.llm.schemas as schemas

# The wire schemas under drift-lock: (wire-dict attr, model attr). The tracer
# seeds the headline pair; plan 06-02 (Task 2) completes the quartet with the
# sobre/experiencias/skills pairs.
WIRES_AND_MODELS = [
    ("LINKEDIN_HEADLINE_STRICT_SCHEMA", "LinkedinHeadline"),
]


def _sym(name: str):
    """Resolve a planned schema symbol at test time — a missing symbol is a
    FAILED assertion about planned behavior, not a collection crash."""
    if not hasattr(schemas, name):
        pytest.fail(f"planned symbol missing from app.llm.schemas: {name}")
    return getattr(schemas, name)


# ---------------------------------------------------------------------------
# Drift-lock — wire dict ↔ Pydantic model (bidirectional, T-02-08/T-06-02)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "LinkedinHeadline",
        "LINKEDIN_HEADLINE_STRICT_SCHEMA",
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


def test_strict_shape_every_object_level_linkedin_wire_schemas() -> None:
    # Pattern 2/A2: additionalProperties:false + ALL properties in required,
    # at EVERY object level of every hand-maintained LinkedIn wire dict.
    for wire_name, _ in WIRES_AND_MODELS:
        wire = _sym(wire_name)
        for obj in _objects(wire):
            assert obj["additionalProperties"] is False, (wire_name, obj)
            assert sorted(obj["required"]) == sorted(obj["properties"]), (wire_name, obj)


def test_wire_schema_top_level_properties_match_pydantic() -> None:
    for wire_name, model_name in WIRES_AND_MODELS:
        wire = _sym(wire_name)
        model = _sym(model_name)
        assert set(wire["properties"]) == set(model.model_json_schema()["properties"]), (
            wire_name,
            model_name,
        )


def test_gateway_registers_linkedin_headline_exactly_once() -> None:
    # The tracer's ONLY gateway edit — one registration, wired to the same
    # wire dict + model this file drift-locks (D-09).
    from app.llm.gateway import _STAGE_SCHEMAS

    entries = [k for k in _STAGE_SCHEMAS if k == "linkedin-headline"]
    assert entries == ["linkedin-headline"]
    model, wire = _STAGE_SCHEMAS["linkedin-headline"]
    assert model is _sym("LinkedinHeadline")
    assert wire is _sym("LINKEDIN_HEADLINE_STRICT_SCHEMA")


# ---------------------------------------------------------------------------
# Strict-model behavior — extra="forbid" + the D-07 no-length-bound contract
# ---------------------------------------------------------------------------


def test_linkedin_headline_accepts_valid_payload() -> None:
    LinkedinHeadline = _sym("LinkedinHeadline")
    parsed = LinkedinHeadline.model_validate({"headline": "Engenheira de dados sênior"})
    assert parsed.headline == "Engenheira de dados sênior"


def test_linkedin_headline_rejects_undeclared_key() -> None:
    LinkedinHeadline = _sym("LinkedinHeadline")
    with pytest.raises(ValidationError) as excinfo:
        LinkedinHeadline.model_validate({"headline": "x", "extra": 1})
    assert "extra" in str(excinfo.value)  # extra="forbid" — unknown keys fail loudly


def test_linkedin_headline_accepts_oversized_string() -> None:
    # D-07 regression guard: a 500-char headline (well over the 220 constant)
    # validates CLEANLY — no per-field length bound may ever leak into the
    # LLM layer, or the gateway would retry-and-abort over-limit runs.
    LinkedinHeadline = _sym("LinkedinHeadline")
    oversized = "h" * 500
    parsed = LinkedinHeadline.model_validate({"headline": oversized})
    assert parsed.headline == oversized
    assert len(parsed.headline) == 500
