"""Master profile schema — minimal strict slice (expanded to the full D-07 set
by plan 02; the architecture established here does not change).

Conventions (see .planning/phases/01 CONTEXT.md):
- D-01/D-04: localized content is a language->text map with base language pt-BR.
- D-02: narrative fields AND job titles are localized; company/dates/contact stay single-value.
- D-10: unknown keys are rejected loudly — every model inherits _Strict (extra="forbid").
- D-11: `example: true` in frontmatter marks placeholder data; it MUST be declared
  here or extra="forbid" rejects the shipped file.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

Language = Literal["pt-BR", "en"]
BASE_LANGUAGE: Language = "pt-BR"  # D-04
LocalizedText = dict[Language, str]  # D-01


class _Strict(BaseModel):
    """Base for ALL profile models — unknown keys fail loudly (D-10)."""

    model_config = ConfigDict(extra="forbid")


def _date_to_str(v: object) -> object:
    # Pitfall 1: unquoted YAML dates arrive as datetime.date objects
    return v.isoformat()[:7] if isinstance(v, date) else v


class Impact(_Strict):
    action: LocalizedText
    metric: LocalizedText
    context: LocalizedText | None = None


class Experience(_Strict):
    company: str  # single-value per D-02: proper noun
    title: LocalizedText  # D-02: job titles ARE localized
    start_date: str
    end_date: str | None = None
    description: LocalizedText
    impacts: list[Impact] = []  # D-08: embedded per experience
    _norm_dates = field_validator("start_date", "end_date", mode="before")(_date_to_str)


class Profile(_Strict):
    example: bool = False  # D-11 — placeholder flag; must be declared (Pitfall 3)
    name: str
    contact: dict[str, str]
    summary: LocalizedText
    experiences: list[Experience]
