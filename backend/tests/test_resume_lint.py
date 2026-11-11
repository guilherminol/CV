"""JD-tied completeness lint tests (PROFILE-02, D-04 a/b/c).

Pure-function tests over validated typed inputs — offline, no I/O, no LLM.
Template strings are pinned character-for-character against the UI-SPEC
Copywriting Contract (backend owns the strings; the frontend renders them
verbatim). The lint is NON-BLOCKING (D-03): it returns an ordered list of
PT-BR avisos and never raises on data gaps.
"""

from conftest import full_profile, minimal_profile

from app.llm.schemas import Keyword
from app.profile.models import Profile
from app.resume.lint import lint_gaps, lint_jd_tied


def _kw(
    canonical: str,
    category: str = "competencias",
    aliases: list[str] | None = None,
    pt: str | None = None,
    en: str | None = None,
) -> Keyword:
    return Keyword.model_validate(
        {
            "canonical": canonical,
            "aliases": aliases or [],
            "pt": pt,
            "en": en,
            "category": category,
        }
    )


# ---------------------------------------------------------------------------
# (a) keyword gaps — competencias/ferramentas vs the profile inventory
# ---------------------------------------------------------------------------


def test_clean_profile_with_inventory_keywords_yields_no_avisos() -> None:
    profile = Profile.model_validate(full_profile())
    keywords = [
        _kw("Python", "competencias", pt="Python", en="Python"),
        _kw("TypeScript", "competencias", pt="TypeScript", en="TypeScript"),
        _kw("Docker", "ferramentas", pt="Docker", en="Docker"),
        _kw("AWS", "ferramentas", pt="AWS", en="AWS"),
    ]
    assert lint_jd_tied(profile, keywords) == []


def test_absent_keyword_is_flagged_with_exact_template() -> None:
    profile = Profile.model_validate(full_profile())
    keywords = [_kw("Snowflake", "ferramentas")]
    assert lint_jd_tied(profile, keywords) == [
        'A vaga cita "Snowflake", ausente do seu perfil.'
    ]


def test_any_rendering_match_prevents_flagging() -> None:
    # canonical "Containerização" is nowhere in the inventory, but the pt
    # rendering "Docker" is — the check matches ANY rendering.
    profile = Profile.model_validate(full_profile())
    keywords = [_kw("Containerização", "ferramentas", pt="Docker")]
    assert lint_jd_tied(profile, keywords) == []


def test_project_technologies_are_an_inventory_surface() -> None:
    data = full_profile()
    # Remove FastAPI from the skills groups; it survives only in the
    # project's technologies — still inventory per D-04a.
    data["skills"] = [{"category": "linguagens", "items": ["Python", "TypeScript"]}]
    profile = Profile.model_validate(data)
    keywords = [_kw("FastAPI", "ferramentas")]
    assert lint_jd_tied(profile, keywords) == []


def test_spoken_language_is_an_inventory_surface() -> None:
    """A vaga citing "English" must NOT flag when the profile speaks Inglês —
    the languages section (name + level, both renderings) is inventory."""
    data = full_profile()
    data["skills"] = [{"category": "linguagens", "items": ["Python", "TypeScript"]}]
    profile = Profile.model_validate(data)
    assert lint_jd_tied(profile, [_kw("English", "competencias")]) == []
    assert lint_jd_tied(profile, [_kw("Inglês", "competencias")]) == []
    # control: a language the profile does NOT speak stays a gap.
    gaps = lint_jd_tied(profile, [_kw("Mandarim", "competencias")])
    assert len(gaps) == 1


def test_titles_and_certifications_categories_are_not_checked() -> None:
    # D-04a scopes the keyword-gap check to competencias + ferramentas only.
    profile = Profile.model_validate(full_profile())
    keywords = [
        _kw("Engenheiro de Dados", "titulos_de_vaga"),
        _kw("PMP", "certificacoes"),
    ]
    assert lint_jd_tied(profile, keywords) == []


# ---------------------------------------------------------------------------
# (b) experiences without impacts
# ---------------------------------------------------------------------------


def test_experience_without_impacts_is_flagged_with_exact_template() -> None:
    data = full_profile()
    data["experiences"][0]["impacts"] = []
    profile = Profile.model_validate(data)
    assert lint_jd_tied(profile, []) == [
        '"Exemplo IA" não tem impactos com métricas no perfil.'
    ]


def test_each_impactless_experience_is_flagged() -> None:
    data = full_profile()
    data["experiences"][0]["impacts"] = []
    data["experiences"].append(
        {
            "company": "Outra Tech",
            "title": {"pt-BR": "Dev", "en": "Dev"},
            "start_date": "2020-01",
            "description": {"pt-BR": "Desc.", "en": "Desc."},
            "impacts": [],
        }
    )
    profile = Profile.model_validate(data)
    avisos = lint_jd_tied(profile, [])
    assert avisos == [
        '"Exemplo IA" não tem impactos com métricas no perfil.',
        '"Outra Tech" não tem impactos com métricas no perfil.',
    ]


# ---------------------------------------------------------------------------
# (c) summary absent or resolving empty
# ---------------------------------------------------------------------------


def test_empty_summary_is_flagged_with_exact_template() -> None:
    data = full_profile()
    data["summary"] = {"pt-BR": "", "en": "   "}  # base language present, resolves empty
    profile = Profile.model_validate(data)
    assert lint_jd_tied(profile, []) == ["O resumo do perfil está vazio."]


# ---------------------------------------------------------------------------
# Ordering (a) → (b) → (c) and non-blocking behavior (D-03)
# ---------------------------------------------------------------------------


def test_gaps_render_in_order_a_then_b_then_c() -> None:
    data = full_profile()
    data["experiences"][0]["impacts"] = []
    data["summary"] = {"pt-BR": ""}
    profile = Profile.model_validate(data)
    keywords = [
        _kw("Snowflake", "ferramentas"),
        _kw("Airflow", "ferramentas"),
    ]
    assert lint_jd_tied(profile, keywords) == [
        'A vaga cita "Snowflake", ausente do seu perfil.',
        'A vaga cita "Airflow", ausente do seu perfil.',
        '"Exemplo IA" não tem impactos com métricas no perfil.',
        "O resumo do perfil está vazio.",
    ]


def test_returns_a_list_on_every_gap_combination() -> None:
    # Non-blocking (D-03): the lint never raises on data gaps.
    profile = Profile.model_validate(minimal_profile())
    assert isinstance(lint_jd_tied(profile, []), list)
    assert isinstance(lint_jd_tied(profile, [_kw("Anything", "competencias")]), list)
    assert lint_jd_tied(profile, []) == []  # minimal profile: summary + impacts present


# ---------------------------------------------------------------------------
# structured gaps — the vaga → perfil acceptance supply (POST body shape)
# ---------------------------------------------------------------------------


def test_lint_gaps_carry_acceptance_payload_and_verbatim_aviso() -> None:
    profile = Profile.model_validate(full_profile())
    keywords = [
        _kw("Snowflake", "ferramentas"),
        _kw("Python", "competencias", pt="Python", en="Python"),  # in inventory
    ]
    gaps = lint_gaps(profile, keywords)
    assert gaps == [
        {
            "canonical": "Snowflake",
            "pt": None,
            "en": None,
            "categoria": "ferramentas",
            "aviso": 'A vaga cita "Snowflake", ausente do seu perfil.',
        }
    ]


def test_lint_gaps_empty_when_inventory_covers_all() -> None:
    profile = Profile.model_validate(full_profile())
    keywords = [_kw("Python", "competencias", pt="Python", en="Python")]
    assert lint_gaps(profile, keywords) == []


def test_gap_aviso_lines_are_exactly_the_jd_tied_avisos_prefix() -> None:
    """One template, two consumers: the structured rows' aviso strings are
    byte-identical to the (a) block of lint_jd_tied's output."""
    profile = Profile.model_validate(full_profile())
    keywords = [_kw("Snowflake", "ferramentas")]
    gaps = lint_gaps(profile, keywords)
    avisos = lint_jd_tied(profile, keywords)
    assert avisos == [gap["aviso"] for gap in gaps]
