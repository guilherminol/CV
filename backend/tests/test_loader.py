"""Loader tests — every failure mode is a loud ProfileError naming the file (SC2).

RED-first (plan 01-02 Task 2): the PT-BR rendering tests assert the D-14 error
style that the interim plan-01 renderer does not produce yet — they MUST fail;
the failure-mode tests pin behaviors the tracer already delivered.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.profile.errors import _ptbr_message, render_errors_ptbr, render_loc
from app.profile.loader import ProfileError, load_profile
from app.profile.models import Profile


# ---------------------------------------------------------------------------
# Failure modes → loud ProfileError (tracer regressions)
# ---------------------------------------------------------------------------


def test_malformed_yaml_is_loud_and_names_file(broken_yaml_profile_path) -> None:
    with pytest.raises(ProfileError) as excinfo:
        load_profile(broken_yaml_profile_path)
    msg = excinfo.value.message_ptbr
    assert "YAML do frontmatter inválido" in msg
    assert str(broken_yaml_profile_path) in msg  # SC2: the exact file is named
    assert excinfo.value.raw  # terminal-only detail preserved


def test_missing_file_names_path(tmp_path) -> None:
    missing = tmp_path / "nao-existe.md"
    with pytest.raises(ProfileError) as excinfo:
        load_profile(missing)
    assert excinfo.value.message_ptbr == f"Perfil não encontrado: {missing}"


def test_non_utf8_bytes_loud_ptbr(non_utf8_profile_path) -> None:
    with pytest.raises(ProfileError) as excinfo:
        load_profile(non_utf8_profile_path)
    msg = excinfo.value.message_ptbr
    assert str(non_utf8_profile_path) in msg
    assert "UTF-8" in msg  # Pitfall 7: encoding failure is a named, PT-BR error


# ---------------------------------------------------------------------------
# ValidationError rendering → PT-BR D-14 lines (RED: interim renderer fails)
# ---------------------------------------------------------------------------


def test_validation_error_message_starts_with_file(typo_profile_path) -> None:
    with pytest.raises(ProfileError) as excinfo:
        load_profile(typo_profile_path)
    assert excinfo.value.message_ptbr.startswith(f"Erro no perfil: {typo_profile_path}")


def test_typo_key_renders_ptbr_extra_forbidden(typo_profile_path) -> None:
    with pytest.raises(ProfileError) as excinfo:
        load_profile(typo_profile_path)
    msg = excinfo.value.message_ptbr
    assert "experiances" in msg  # the exact bad key text
    assert "chave desconhecida" in msg  # PT-BR phrase — not the English dump
    assert "extra_forbidden" not in msg  # internal type names stay out of the UI path
    assert "Extra inputs are not permitted" not in msg  # anti-pattern: English prose


def test_nested_typo_renders_d14_loc_path(nested_typo_profile_path) -> None:
    with pytest.raises(ProfileError) as excinfo:
        load_profile(nested_typo_profile_path)
    assert "experiences[0].salario" in excinfo.value.message_ptbr


def test_missing_base_language_renders_estrutura_do_perfil(missing_ptbr_profile_path) -> None:
    with pytest.raises(ProfileError) as excinfo:
        load_profile(missing_ptbr_profile_path)
    msg = excinfo.value.message_ptbr
    assert "estrutura do perfil" in msg  # Pitfall 8: empty loc → structure-level
    assert "idioma base 'pt-BR' ausente" in msg  # validator's own PT-BR passes through


def test_value_error_renders_without_english_prefix(missing_ptbr_profile_path) -> None:
    """WR-02: Pydantic's English 'Value error, ' prefix never reaches the UI (D-14)."""
    with pytest.raises(ProfileError) as excinfo:
        load_profile(missing_ptbr_profile_path)
    msg = excinfo.value.message_ptbr
    assert "Value error, " not in msg  # the English prefix is stripped
    assert "idioma base 'pt-BR' ausente" in msg  # the validator's PT-BR survives intact


def test_raw_keeps_full_error_detail(typo_profile_path) -> None:
    with pytest.raises(ProfileError) as excinfo:
        load_profile(typo_profile_path)
    assert "extra_forbidden" in excinfo.value.raw  # internal detail in the terminal channel


# ---------------------------------------------------------------------------
# render_loc — the D-14 path format, unit-level
# ---------------------------------------------------------------------------


def test_render_loc_d14_paths() -> None:
    assert render_loc(("experiences", 2, "data_fim")) == "experiences[2].data_fim"
    assert render_loc(()) == "estrutura do perfil"  # Pitfall 8: empty loc
    assert render_loc(("contact", "email")) == "contact.email"


def test_render_loc_language_key_marker() -> None:
    # Verified loc shape for literal_error on a localized-map key:
    loc = ("experiences", 0, "title", "values", "pt-PT", "[key]")
    assert render_loc(loc) == "experiences[0].title.values.pt-PT (chave)"


# ---------------------------------------------------------------------------
# WR-01: every producible Pydantic error type renders PT-BR — the UI path
# never shows English prose (D-14). RED: unmapped types leak e["msg"].
# ---------------------------------------------------------------------------


def _render_validation_error(data: dict) -> str:
    """Validate `data` against Profile and render the errors exactly as the API does."""
    try:
        Profile.model_validate(data)
    except ValidationError as exc:
        return render_errors_ptbr(exc, Path("profile.md"))
    raise AssertionError("esperado ValidationError para os dados quebrados")


def test_model_list_and_dict_type_errors_render_ptbr(minimal_profile_data: dict) -> None:
    minimal_profile_data["contact"] = "texto"
    minimal_profile_data["experiences"] = "ops"
    minimal_profile_data["summary"] = "texto"
    msg = _render_validation_error(minimal_profile_data)
    assert "contact — estrutura esperada (bloco de dados), encontrado valor simples" in msg
    assert "experiences — lista esperada, encontrado valor de outro tipo" in msg
    assert "summary — dicionário esperado, encontrado valor de outro tipo" in msg
    assert "Input should be" not in msg  # English Pydantic prose never reaches the UI


def test_bool_parsing_error_renders_ptbr(minimal_profile_data: dict) -> None:
    minimal_profile_data["example"] = "talvez"
    msg = _render_validation_error(minimal_profile_data)
    assert "example — verdadeiro/falso esperado, encontrado texto não reconhecido" in msg
    assert "unable to interpret" not in msg  # the raw English msg stays out of the UI path


def test_unmapped_error_type_falls_back_to_ptbr_template() -> None:
    """A future/unmapped type still renders PT-BR — never raw English (D-14)."""
    msg = _ptbr_message({"type": "algum_tipo_futuro", "msg": "Input should be valid"})
    assert "valor inválido para este campo" in msg
    assert "Input should be valid" not in msg


# ---------------------------------------------------------------------------
# The shipped example persona (SC3 data half + SC4 bilingual proof)
# ---------------------------------------------------------------------------


def test_shipped_profile_validates(shipped_profile_path) -> None:
    """The shipped content/profile.md validates against the FULL schema —
    it now carries the owner's real data (example: false since the real
    profile landed), so the old example-persona shape pins are gone; what
    must hold forever is that the owner-edited file parses clean."""
    profile = load_profile(shipped_profile_path)  # any key mismatch fails via extra=forbid
    assert profile.name  # parsed profile object is present
    assert profile.experiences  # SC3 data half: experiences present
    assert all(exp.impacts for exp in profile.experiences)  # D-08: impacts embedded
    assert all(exp.title.get("pt-BR") and exp.title.get("en") for exp in profile.experiences)
    assert profile.education and profile.certifications and profile.languages
