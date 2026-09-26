"""Loader tests — every failure mode is a loud ProfileError naming the file (SC2).

RED-first (plan 01-02 Task 2): the PT-BR rendering tests assert the D-14 error
style that the interim plan-01 renderer does not produce yet — they MUST fail;
the failure-mode tests pin behaviors the tracer already delivered.
"""

import pytest

from app.profile.errors import render_loc
from app.profile.loader import ProfileError, load_profile


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
