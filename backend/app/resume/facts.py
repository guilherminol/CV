"""Profile-fact serialization — the grounding supply line (RESUME-03, D-07).

Pure functions: no I/O, no imports beyond app.profile.models. Everything the
resume stages receive as FATOS DO PERFIL is emitted here, and the serializer
emits ONLY profile-derived values — the fixed uppercase section/field labels
are the only non-profile strings in the blob. The prompts' hard rule (D-07:
rephrase, never invent) is enforceable precisely because this blob is the
model's sole source of truth.

LocalizedText resolution mirrors the ProfilePreview display convention
extended for run language (UI-SPEC Zone 4): the run language's value when
present and non-empty, pt-BR fallback (the declared base language, guaranteed
by the schema), else the first non-empty value; an empty/None map renders "".
"""

from app.profile.models import Impact, Profile


def resolve_loc(values: dict[str, str] | None, language: str) -> str:
    """Run-language value with pt-BR fallback, else the first non-empty value.

    Empty strings never win; an empty/None map returns "" (the profile schema
    guarantees pt-BR exists, so this is defensive for partial dicts in tests).
    """
    if not values:
        return ""
    candidate = values.get(language)
    if isinstance(candidate, str) and candidate.strip():
        return candidate
    base = values.get("pt-BR")
    if isinstance(base, str) and base.strip():
        return base
    for value in values.values():
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _impact_line(impact: Impact, language: str) -> str:
    """One profile impact as "ação — métrica (contexto)" (D-08); the context
    part is omitted when the profile carries none."""
    line = f"{resolve_loc(impact.action, language)} — {resolve_loc(impact.metric, language)}"
    context = resolve_loc(impact.context, language)
    if context:
        line += f" ({context})"
    return line


def _section(title: str, blocks: list[str]) -> str | None:
    """Join labeled blocks under a fixed uppercase section title; None skips
    the section entirely so empty optional sections never appear in the blob."""
    if not blocks:
        return None
    return title + ":\n" + "\n\n".join(blocks)


def serialize_profile_facts(profile: Profile, language: str) -> str:
    """One labeled multi-section text blob — the FATOS DO PERFIL.

    Section/field labels are fixed PT-BR strings; every value is
    profile-derived, resolved to the run language with pt-BR fallback.
    """
    sections: list[str] = []

    contact_lines = [
        f"NOME: {profile.name}",
        f"EMAIL: {profile.contact.email}",
    ]
    if profile.contact.location:
        contact_lines.append(f"LOCAL: {profile.contact.location}")
    if profile.contact.phone:
        contact_lines.append(f"TELEFONE: {profile.contact.phone}")
    if profile.contact.linkedin:
        contact_lines.append(f"LINKEDIN: {profile.contact.linkedin}")
    sections.append(_section("DADOS DE CONTATO", contact_lines))

    summary = resolve_loc(profile.summary, language)
    if summary:
        sections.append(_section("RESUMO ATUAL", [summary]))

    experience_blocks: list[str] = []
    for exp in profile.experiences:
        if exp.end_date:
            period = f"{exp.start_date} – {exp.end_date}"
        else:
            period = f"{exp.start_date} – atual"
        lines = [
            f"cargo: {resolve_loc(exp.title, language)}",
            f"empresa: {exp.company}",
        ]
        if exp.location:
            lines.append(f"local: {exp.location}")
        lines.append(f"período: {period}")
        lines.append(f"descrição: {resolve_loc(exp.description, language)}")
        for impact in exp.impacts:
            lines.append(_impact_line(impact, language))
        experience_blocks.append("\n".join(lines))
    sections.append(_section("EXPERIÊNCIAS", experience_blocks))

    education_blocks: list[str] = []
    for edu in profile.education:
        lines = [
            f"instituição: {edu.institution}",
            f"grau: {edu.degree}",
        ]
        if edu.start_date:
            end = edu.end_date if edu.end_date else "atual"
            lines.append(f"período: {edu.start_date} – {end}")
        elif edu.end_date:
            lines.append(f"conclusão: {edu.end_date}")
        education_blocks.append("\n".join(lines))
    sections.append(_section("FORMAÇÃO", education_blocks))

    skills_blocks = [
        f"{group.category}: {', '.join(group.items)}"
        for group in profile.skills
        if group.items
    ]
    sections.append(_section("HABILIDADES", skills_blocks))

    certification_blocks: list[str] = []
    for cert in profile.certifications:
        line = cert.name
        detail = " — ".join(part for part in (cert.issuer, cert.year) if part)
        certification_blocks.append(f"{line} — {detail}" if detail else line)
    sections.append(_section("CERTIFICAÇÕES", certification_blocks))

    language_blocks = [f"{entry.name}: {entry.level}" for entry in profile.languages]
    sections.append(_section("IDIOMAS", language_blocks))

    project_blocks: list[str] = []
    for project in profile.projects:
        lines = [f"nome: {project.name}"]
        description = resolve_loc(project.description, language)
        if description:
            lines.append(f"descrição: {description}")
        if project.technologies:
            lines.append(f"tecnologias: {', '.join(project.technologies)}")
        for impact in project.impacts:
            lines.append(_impact_line(impact, language))
        project_blocks.append("\n".join(lines))
    sections.append(_section("PROJETOS", project_blocks))

    return "\n\n".join(section for section in sections if section)


def compose_stage_input(facts: str, jd_text: str) -> str:
    """The single input blob a resume run passes as run_stage input_text: the
    profile-fact section plus the pasted job description — both DATA inside
    the gateway's existing user-message template (T-02-01), never plumbing."""
    return (
        "FATOS DO PERFIL:\n"
        f"{facts}\n"
        "\n"
        "DESCRIÇÃO DA VAGA:\n"
        f"{jd_text}"
    )
