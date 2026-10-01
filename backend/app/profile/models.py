"""Master profile schema — full v1 (D-01…D-11).

Conventions (see .planning/phases/01 CONTEXT.md):
- D-01/D-04: localized content is a language->text map with base language pt-BR.
- D-02: narrative fields AND job titles are localized; company/dates/contact stay single-value.
- D-03/D-04: every localized field must carry the base language pt-BR
  (enforced by _BaseLanguageMixin); other languages are optional.
- D-07: full resume section set — contact, summary, experiences, education,
  skills, certifications, languages, projects.
- D-08: impacts are embedded per experience/project entry.
- D-09: skills are categorized groups of plain tech names.
- D-10: unknown keys are rejected loudly — every model inherits _Strict
  (extra="forbid"); model_config is per-class, so EVERY model must inherit it.
- D-11: `example: true` in frontmatter marks placeholder data; it MUST be
  declared here or extra="forbid" rejects the shipped file.
"""

import re
from datetime import date
from typing import Literal, Self, get_args

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

Language = Literal["pt-BR", "en"]
BASE_LANGUAGE: Language = "pt-BR"  # D-04
LocalizedText = dict[Language, str]  # D-01


class _Strict(BaseModel):
    """Base for ALL profile models — unknown keys fail loudly (D-10)."""

    model_config = ConfigDict(extra="forbid")


# WR-03: dates are stored at month precision, "AAAA-MM" (ex.: 2022-03).
# Unquoted YAML dates arrive as datetime.date (Pitfall 1) and are truncated;
# any string that is not already "AAAA-MM" fails loudly so typo'd dates can
# never pass silently and the stored format stays uniform for downstream
# consumers (experience sorting, PDF output).
_DATE_RE = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])")


def _date_to_str(v: object) -> object:
    if isinstance(v, date):  # Pitfall 1: unquoted YAML dates arrive as datetime.date
        return v.isoformat()[:7]
    if isinstance(v, str) and not _DATE_RE.fullmatch(v):
        raise ValueError(
            f"data esperada no formato 'AAAA-MM' (ex.: 2022-03), encontrado '{v}'"
        )
    return v


def _is_localized(annotation: object) -> bool:
    """True for `LocalizedText` and `LocalizedText | None` annotations.

    Compares structurally (==), not by identity: Pydantic's stored FieldInfo
    annotation can be an equal-but-not-identical generic alias object.
    """
    return annotation == LocalizedText or LocalizedText in get_args(annotation)


class _BaseLanguageMixin(BaseModel):
    """D-03/D-04: every localized field must carry the base language pt-BR.

    The ValueError names the offending field; Pydantic surfaces it as
    type=value_error with an EMPTY loc (Pitfall 8) — the error renderer maps
    that to "estrutura do perfil". Composition through inheritance is
    assumption A4: test_base_language_required_* catches a silent absence
    immediately; the verified fallback is duplicating the validator per model.
    """

    @model_validator(mode="after")
    def _base_language_present(self) -> "Self":
        for name, field in type(self).model_fields.items():
            if not _is_localized(field.annotation):
                continue
            values = getattr(self, name)
            if values is None:
                continue  # optional localized field absent — base rule does not apply
            if isinstance(values, str):
                continue  # `str | LocalizedText` union: a brand str IS the whole value
            if BASE_LANGUAGE not in values:
                raise ValueError(
                    f"idioma base '{BASE_LANGUAGE}' ausente no campo localizado "
                    f"'{name}' — adicione ao menos a chave '{BASE_LANGUAGE}'"
                )
        return self


class Contact(_BaseLanguageMixin, _Strict):
    """D-07 contact block. Email and LinkedIn are language-neutral single
    values; location and phone ARE localized (D-02 pattern — both render on
    sendable documents: "Brasil"/"Brazil", local vs +55 phone format)."""

    email: str
    location: LocalizedText | None = None
    phone: LocalizedText | None = None
    linkedin: str | None = None


class Impact(_BaseLanguageMixin, _Strict):
    """D-08 impact line — narrative, therefore localized (D-02)."""

    action: LocalizedText
    metric: LocalizedText
    context: LocalizedText | None = None


class Experience(_BaseLanguageMixin, _Strict):
    """Work experience with embedded impacts (D-08)."""

    company: str  # single-value per D-02: proper noun
    title: LocalizedText  # D-02: job titles ARE localized
    location: str | None = None
    start_date: str
    end_date: str | None = None
    description: LocalizedText
    impacts: list[Impact] = []  # D-08: embedded per experience
    _norm_dates = field_validator("start_date", "end_date", mode="before")(_date_to_str)


class EducationEntry(_BaseLanguageMixin, _Strict):
    """Work-history education entry; the degree IS localized (D-02 pattern —
    it renders on sendable documents in the run language)."""

    institution: str  # single-value per D-02: proper noun
    degree: LocalizedText
    start_date: str | None = None
    end_date: str | None = None
    _norm_dates = field_validator("start_date", "end_date", mode="before")(_date_to_str)


class SkillGroup(_BaseLanguageMixin, _Strict):
    """D-09: categorized group of plain tech names (single-value, D-02)."""

    category: str
    items: list[str]


class CertificationEntry(_BaseLanguageMixin, _Strict):
    """Certification entry; the name is a single-value proper noun, but the
    issuer IS localized (D-02 pattern — the issuer line may carry the
    certificate's nature, e.g. course completion vs exam, per language)."""

    name: str
    issuer: LocalizedText | None = None
    year: str | None = None


class LanguageEntry(_BaseLanguageMixin, _Strict):
    """Language name and proficiency ARE localized (D-02 pattern — both render
    on sendable documents in the run language)."""

    name: LocalizedText
    level: LocalizedText


class Project(_BaseLanguageMixin, _Strict):
    """D-08 pattern applied to projects: embedded impacts per project.

    name: brand str OR localized map — a title may carry a per-language
    descriptor ("Financeiro — Gestão pessoal..." / "— Personal finance...").
    scope separates in-company (profissional) from personal projects so the
    document groups them honestly instead of mixing employers with side
    projects."""

    name: str | LocalizedText
    scope: Literal["profissional", "pessoal"]
    description: LocalizedText
    technologies: list[str] = []
    impacts: list[Impact] = []


class Profile(_BaseLanguageMixin, _Strict):
    """Root of the master profile — the full D-07 section set."""

    example: bool = False  # D-11 — placeholder flag; must be declared (Pitfall 3)
    name: str
    contact: Contact  # typed (was dict[str, str] in the plan-01 tracer slice)
    summary: LocalizedText
    experiences: list[Experience]
    education: list[EducationEntry] = []
    skills: list[SkillGroup] = []
    certifications: list[CertificationEntry] = []
    languages: list[LanguageEntry] = []
    projects: list[Project] = []
