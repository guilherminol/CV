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
# (Task 1) seeded the headline pair; Task 2 completes the quartet — ALL FOUR
# LinkedIn blocks are drift-locked and over-limit-safe before any expansion
# wave starts (D-09).
WIRES_AND_MODELS = [
    ("LINKEDIN_HEADLINE_STRICT_SCHEMA", "LinkedinHeadline"),
    ("LINKEDIN_SOBRE_STRICT_SCHEMA", "LinkedinSobre"),
    ("LINKEDIN_EXPERIENCIAS_STRICT_SCHEMA", "LinkedinExperiencias"),
    ("LINKEDIN_SKILLS_STRICT_SCHEMA", "LinkedinSkills"),
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
        "LinkedinSobre",
        "ExperienciaLinkedin",
        "LinkedinExperiencias",
        "LinkedinSkills",
        "LINKEDIN_HEADLINE_STRICT_SCHEMA",
        "LINKEDIN_SOBRE_STRICT_SCHEMA",
        "LINKEDIN_EXPERIENCIAS_STRICT_SCHEMA",
        "LINKEDIN_SKILLS_STRICT_SCHEMA",
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


def test_linkedin_experiencias_nested_item_properties_match_pydantic() -> None:
    wire = _sym("LINKEDIN_EXPERIENCIAS_STRICT_SCHEMA")
    ExperienciaLinkedin = _sym("ExperienciaLinkedin")
    wire_items = wire["properties"]["experiencias"]["items"]["properties"]
    pyd_items = ExperienciaLinkedin.model_json_schema()["properties"]
    assert set(wire_items) == set(pyd_items)  # names match at the nested level too


def test_only_the_tracer_stage_is_registered_in_the_gateway() -> None:
    # Plan 06-01 Task 2: the three new stages are NOT registered yet — the
    # stages land with their prompt files in 06-02 (registration without a
    # prompt file would make any accidental call fail at the loader; keep the
    # tracer's registration surface minimal).
    from app.llm.gateway import _STAGE_SCHEMAS

    assert "linkedin-headline" in _STAGE_SCHEMAS
    for stage in ("linkedin-sobre", "linkedin-experiencias", "linkedin-skills"):
        assert stage not in _STAGE_SCHEMAS, stage


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


# ---------------------------------------------------------------------------
# D-07 oversize guards — NO length bound may ever leak into the LLM layer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("model_name", "payload", "text"),
    [
        # 500-char headline (limit 220), 3000-char sobre (limit 2600),
        # 2500-char descricao (limit 2000), 150-item habilidades
        # (soft official count bound 100 — also NOT a validation bound here).
        (
            "LinkedinHeadline",
            lambda text: {"headline": text},
            "h" * 500,
        ),
        (
            "LinkedinSobre",
            lambda text: {"sobre": text},
            "s" * 3000,
        ),
        (
            "ExperienciaLinkedin",
            lambda text: {"company": "Exemplo IA", "title": "Engenheira", "descricao": text},
            "d" * 2500,
        ),
        (
            "LinkedinExperiencias",
            lambda text: {
                "experiencias": [
                    {"company": "Exemplo IA", "title": "Engenheira", "descricao": text}
                ]
            },
            "d" * 2500,
        ),
    ],
)
def test_oversize_strings_validate_cleanly_no_length_bound_leaks(
    model_name: str, payload, text: str
) -> None:
    # Research Pitfall 1 / D-07: a max_length here converts the over-limit
    # FLAG path into a hard run failure via the gateway retry ladder. Each
    # model must ACCEPT its over-limit input intact.
    model = _sym(model_name)
    parsed = model.model_validate(payload(text))
    dumped = parsed.model_dump()
    if "headline" in dumped:
        assert dumped["headline"] == text
    elif "sobre" in dumped:
        assert dumped["sobre"] == text
    elif "descricao" in dumped:  # the flat entry model
        assert dumped["descricao"] == text
    else:  # the wrapper model
        assert dumped["experiencias"][0]["descricao"] == text


def test_skills_list_accepts_over_count_array() -> None:
    # 150 skills — the official count bound (100) is a post-generation sanity
    # check, NEVER an LLM-layer validation bound (same D-07 posture).
    LinkedinSkills = _sym("LinkedinSkills")
    habilidades = [f"skill-{i}" for i in range(150)]
    parsed = LinkedinSkills.model_validate({"habilidades": habilidades})
    assert parsed.habilidades == habilidades
    assert len(parsed.habilidades) == 150


def test_linkedin_models_reject_undeclared_keys() -> None:
    # extra="forbid" everywhere via _Strict (D-06 posture) — spot-check the
    # remaining three models beyond the headline spot-check above.
    for model_name, bad_payload in (
        ("LinkedinSobre", {"sobre": "x", "extra": 1}),
        (
            "ExperienciaLinkedin",
            {"company": "c", "title": "t", "descricao": "d", "extra": 1},
        ),
        ("LinkedinSkills", {"habilidades": ["a"], "extra": 1}),
    ):
        model = _sym(model_name)
        with pytest.raises(ValidationError) as excinfo:
            model.model_validate(bad_payload)
        assert "extra" in str(excinfo.value)
