"""Schema tests — strict rejection, base-language rule, coercions (D-01…D-11).

RED-first (plan 01-02 Task 1): the base-language tests assert enforcement that
does not exist yet and MUST fail; the remaining tests pin behaviors the plan-01
tracer slice already delivered (regression guard).
"""

from datetime import date

import pytest
from pydantic import ValidationError

from app.profile.models import (
    CertificationEntry,
    Contact,
    EducationEntry,
    Experience,
    Impact,
    LanguageEntry,
    Profile,
    Project,
    SkillGroup,
)


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
    # Pitfall 8: model-level errors carry NO field loc — through Profile they
    # hold only the nested-model path prefix (empty loc when the model itself
    # is validated directly, as in the Impact test below).
    assert error["loc"] == ("experiences", 0)
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


# Pitfall 3: one forbid test per nested model — a single forgotten model would
# silently re-enable typo tolerance on exactly that section.


def test_unknown_key_rejected_on_contact() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Contact.model_validate({"email": "ana@example.com", "celular": "123"})
    error = excinfo.value.errors(include_url=False)[0]
    assert error["type"] == "extra_forbidden"
    assert "celular" in error["loc"]


def test_unknown_key_rejected_on_education_entry() -> None:
    with pytest.raises(ValidationError) as excinfo:
        EducationEntry.model_validate(
            {"institution": "Universidade Exemplo", "degree": "BSc", "ano": "2017"}
        )
    error = excinfo.value.errors(include_url=False)[0]
    assert error["type"] == "extra_forbidden"
    assert "ano" in error["loc"]


def test_unknown_key_rejected_on_skill_group() -> None:
    with pytest.raises(ValidationError) as excinfo:
        SkillGroup.model_validate({"category": "linguagens", "items": ["Python"], "nivel": "alto"})
    error = excinfo.value.errors(include_url=False)[0]
    assert error["type"] == "extra_forbidden"
    assert "nivel" in error["loc"]


def test_unknown_key_rejected_on_certification_entry() -> None:
    with pytest.raises(ValidationError) as excinfo:
        CertificationEntry.model_validate({"name": "AWS SA", "ano": "2023"})
    error = excinfo.value.errors(include_url=False)[0]
    assert error["type"] == "extra_forbidden"
    assert "ano" in error["loc"]


def test_unknown_key_rejected_on_language_entry() -> None:
    with pytest.raises(ValidationError) as excinfo:
        LanguageEntry.model_validate({"name": "Inglês", "nivel": "avançado"})
    # `level` is also missing here — pick the extra_forbidden error specifically.
    extra_errors = [
        e for e in excinfo.value.errors(include_url=False) if e["type"] == "extra_forbidden"
    ]
    assert extra_errors, "esperado extra_forbidden para a chave desconhecida"
    assert "nivel" in extra_errors[0]["loc"]


def test_unknown_key_rejected_on_project() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Project.model_validate(
            {
                "name": "Assistente Exemplo",
                "description": {"pt-BR": "d", "en": "d"},
                "tecnologias": ["FastAPI"],
            }
        )
    error = excinfo.value.errors(include_url=False)[0]
    assert error["type"] == "extra_forbidden"
    assert "tecnologias" in error["loc"]


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


# ---------------------------------------------------------------------------
# The shipped example persona — fully bilingual (D-17, SC4)
# ---------------------------------------------------------------------------


def _walk_localized_maps(node: object):
    """Yield every LocalizedText-shaped dict in a model_dump() tree."""
    if isinstance(node, dict):
        if node and set(node.keys()) <= {"pt-BR", "en"}:
            yield node
        else:
            for value in node.values():
                yield from _walk_localized_maps(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_localized_maps(item)


def test_example_fully_bilingual(shipped_profile_path) -> None:
    from app.profile.loader import load_profile

    profile = load_profile(shipped_profile_path)
    localized_maps = list(_walk_localized_maps(profile.model_dump()))
    assert localized_maps, "o exemplo enviado deve conter campos localizados"
    for localized in localized_maps:
        assert "pt-BR" in localized, f"mapa localizado sem pt-BR: {localized}"
        assert "en" in localized, f"mapa localizado sem en: {localized}"
