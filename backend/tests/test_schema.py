"""Schema tests — strict rejection, base-language rule, coercions (D-01…D-11).

RED-first (plan 01-02 Task 1): the base-language tests assert enforcement that
does not exist yet and MUST fail; the remaining tests pin behaviors the plan-01
tracer slice already delivered (regression guard).
"""

from datetime import date

import pytest
from pydantic import ValidationError

from app.profile.models import Experience, Impact, Profile


def _value_error(excinfo: pytest.ExceptionInfo[ValidationError]) -> dict:
    """Return the first value_error entry, failing with context if absent."""
    errors = excinfo.value.errors(include_url=False)
    value_errors = [e for e in errors if e["type"] == "value_error"]
    assert value_errors, (
        f"esperado value_error (idioma base ausente), obtido: "
        f"{[(e['type'], e['msg']) for e in errors]}"
    )
    return value_errors[0]


# ---------------------------------------------------------------------------
# Base-language enforcement (D-03/D-04) — RED: must fail until the mixin lands
# ---------------------------------------------------------------------------


def test_base_language_required_on_experience(minimal_profile_data: dict) -> None:
    data = minimal_profile_data
    data["experiences"][0]["title"] = {"en": "Senior Software Engineer"}
    with pytest.raises(ValidationError) as excinfo:
        Profile.model_validate(data)
    error = _value_error(excinfo)
    assert error["loc"] == ()  # Pitfall 8: model-level errors carry an EMPTY loc
    assert "title" in error["msg"]  # the field is named
    assert "pt-BR" in error["msg"]  # the base language is named


def test_base_language_required_on_impact() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Impact.model_validate(
            {
                "action": {"en": "Implemented a RAG pipeline"},
                "metric": {"pt-BR": "-40% no tempo de resposta", "en": "-40% response time"},
            }
        )
    error = _value_error(excinfo)
    assert "action" in error["msg"]
    assert "pt-BR" in error["msg"]


def test_base_language_required_on_profile_summary(minimal_profile_data: dict) -> None:
    data = minimal_profile_data
    data["summary"] = {"en": "Summary without the base language."}
    with pytest.raises(ValidationError) as excinfo:
        Profile.model_validate(data)
    error = _value_error(excinfo)
    assert "summary" in error["msg"]
    assert "pt-BR" in error["msg"]


# ---------------------------------------------------------------------------
# Unknown-key rejection (D-10) — extra_forbidden, exact key in loc
# ---------------------------------------------------------------------------


def test_unknown_key_rejected_on_profile(minimal_profile_data: dict) -> None:
    data = minimal_profile_data
    data["experiances"] = []  # D-10's canonical typo
    with pytest.raises(ValidationError) as excinfo:
        Profile.model_validate(data)
    error = excinfo.value.errors(include_url=False)[0]
    assert error["type"] == "extra_forbidden"
    assert "experiances" in error["loc"]


def test_unknown_key_rejected_on_experience(minimal_profile_data: dict) -> None:
    data = minimal_profile_data
    data["experiences"][0]["salario"] = "1.000.000"
    with pytest.raises(ValidationError) as excinfo:
        Profile.model_validate(data)
    error = excinfo.value.errors(include_url=False)[0]
    assert error["type"] == "extra_forbidden"
    assert error["loc"] == ("experiences", 0, "salario")


def test_unknown_key_rejected_on_impact(minimal_profile_data: dict) -> None:
    data = minimal_profile_data
    data["experiences"][0]["impacts"] = [
        {
            "action": {"pt-BR": "a", "en": "a"},
            "metric": {"pt-BR": "m", "en": "m"},
            "resultado": "x",
        }
    ]
    with pytest.raises(ValidationError) as excinfo:
        Profile.model_validate(data)
    error = excinfo.value.errors(include_url=False)[0]
    assert error["type"] == "extra_forbidden"
    assert error["loc"] == ("experiences", 0, "impacts", 0, "resultado")


# ---------------------------------------------------------------------------
# Localized map shape: unknown language keys (literal_error)
# ---------------------------------------------------------------------------


def test_unknown_language_key_is_literal_error(minimal_profile_data: dict) -> None:
    data = minimal_profile_data
    data["experiences"][0]["title"] = {"pt-BR": "t", "pt-PT": "t", "en": "e"}
    with pytest.raises(ValidationError) as excinfo:
        Profile.model_validate(data)
    literal_errors = [
        e for e in excinfo.value.errors(include_url=False) if e["type"] == "literal_error"
    ]
    assert literal_errors, "esperado literal_error para chave de idioma desconhecida"
    assert "pt-PT" in literal_errors[0]["loc"]  # the offending key is named exactly
    assert literal_errors[0]["loc"][-1] == "[key]"


# ---------------------------------------------------------------------------
# Date coercion (Pitfall 1) and the example flag (D-11)
# ---------------------------------------------------------------------------


def test_date_coercion_accepts_unquoted_yaml_dates() -> None:
    experience = Experience.model_validate(
        {
            "company": "Exemplo IA",
            "title": {"pt-BR": "t", "en": "t"},
            "start_date": date(2022, 3, 1),  # unquoted YAML dates arrive as datetime.date
            "end_date": date(2023, 5, 20),
            "description": {"pt-BR": "d", "en": "d"},
        }
    )
    assert experience.start_date == "2022-03"
    assert experience.end_date == "2023-05"


def test_example_flag_round_trips(minimal_profile_data: dict) -> None:
    minimal_profile_data["example"] = True
    assert Profile.model_validate(minimal_profile_data).example is True
    minimal_profile_data["example"] = False
    assert Profile.model_validate(minimal_profile_data).example is False
