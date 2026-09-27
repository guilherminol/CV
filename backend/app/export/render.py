"""Export print template (D-03/D-05) — pure HTML builder: no I/O, no template engine.

build_resume_html mirrors the D-05 montage the result screen shows
(ResumeResult.tsx:139-255): name/contact header, then sections in PREVIEW
order — resumo (gerado), experiencias (gerado), formacao (perfil),
habilidades (gerado), certificacoes/idiomas/projetos (perfil); zero-entry
passthrough sections stay hidden (ProfilePreview convention).

Single source of truth (D-03): HEADINGS maps every section key to its
run-language label — gate.py's heading-order check and (plan 04-02) the
selfcheck ordem rows assert against THIS map, never a copy. A2 (Task 0
verdict, confirmed 2026-09-27): ALL 7 headings localize to the run language —
an EN run renders Summary/Experience/Education/Skills/... — a
presentation-only divergence from the in-app PT-BR passthrough-label
convention; content itself still travels verbatim (D-10).

Dates on generated experiences (research Open Questions 1+3):
join_experience_dates joins perfil.experiences to secoes.experiencias by
folded company; matched entries render `format_date_range(start, end)` —
RAW stored strings, "start – end" or "start – atual" (the in-app dateRange()
convention, no locale formatting). Unmatched entries render dateless — no
invented dates, ever.

Safety (V5.3, T-04-01): every data string passes through esc() —
html.escape(quote=True) — so profile/LLM text can never inject markup into
the rendered document (server-side analogue of the JSX-text-children
convention). Pure functions: same inputs → same HTML.

Engine-agnostic CSS (D-01/D-02 reversibility): block layout only — no
flex/grid/floats — declaring BOTH break-inside properties (WeasyPrint
reliably honors the legacy page-break-inside). Headings are written in final
case; NO text-transform anywhere (Pitfall 3: Chromium bakes transformed
glyphs into the PDF text layer).

One traversal, two consumers: _sections_content produces the structured
plain-string content ONCE; build_resume_html renders it (escaping at the
last moment) and iter_rendered_strings flattens it — the exhaustive
accent-integrity universe gate check 4 proves (never sampled).
"""

import html
from dataclasses import dataclass

from app.profile.models import LocalizedText
from app.resume.coverage import _fold

CONTACT_SEPARATOR = " · "  # PREVIEW_CONTACT_SEPARATOR convention (constants/ui.ts)
SKILLS_SEPARATOR = ", "  # ResumeResult renders habilidades.join(', ')
DATE_SEPARATOR = " – "  # dateRange() convention: raw stored strings (Open Question 3)
PRESENT = "atual"  # PREVIEW_PRESENT convention
EM_DASH_SEPARATOR = " — "  # ResumeResult cert/idioma/impact lines

# A2: every section key localizes in BOTH languages — THE shared map (gate +
# plan-04-02 selfcheck ordem import this; never duplicate).
HEADINGS: dict[str, dict[str, str]] = {
    "pt-BR": {
        "resumo": "Resumo",
        "experiencias": "Experiência",
        "formacao": "Formação",
        "habilidades": "Habilidades",
        "certificacoes": "Certificações",
        "idiomas": "Idiomas",
        "projetos": "Projetos",
    },
    "en": {
        "resumo": "Summary",
        "experiencias": "Experience",
        "formacao": "Education",
        "habilidades": "Skills",
        "certificacoes": "Certifications",
        "idiomas": "Languages",
        "projetos": "Projects",
    },
}

# D-05 render order (mirrors ResumeResult.tsx: resumo → experiencias →
# formacao → habilidades → certificacoes → idiomas → projetos).
section_keys: tuple[str, ...] = (
    "resumo",
    "experiencias",
    "formacao",
    "habilidades",
    "certificacoes",
    "idiomas",
    "projetos",
)

_CSS = """
@page { size: A4; margin: 1.6cm; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10.5pt; color: #111111; }
h1 { font-size: 20pt; margin: 0; }
h2 { font-size: 11.5pt; margin: 14pt 0 4pt 0; border-bottom: 0.5pt solid #999999; padding-bottom: 2pt; }
h3 { font-size: 10.5pt; margin: 8pt 0 2pt 0; }
p { margin: 2pt 0; }
ul { margin: 2pt 0; padding-left: 14pt; }
li { margin: 1pt 0; }
section { break-inside: avoid; page-break-inside: avoid; }
.contact { color: #444444; }
.meta { color: #555555; }
"""


def esc(text: str) -> str:
    """Escape EVERY interpolated data string — no exceptions (V5.3, T-04-01)."""
    return html.escape(text, quote=True)


def format_date_range(start: str, end: str | None) -> str:
    """dateRange() convention (ResumeResult.tsx:41-43): raw stored strings;
    open ranges show 'atual'. No locale formatting (Open Question 3)."""
    return f"{start}{DATE_SEPARATOR}{end}" if end else f"{start}{DATE_SEPARATOR}{PRESENT}"


def join_experience_dates(
    perfil, secoes
) -> dict[str, tuple[str, str | None]]:
    """Join perfil.experiences dates onto the generated entries by company.

    Match key: strip + coverage._fold (casefold + NFKD — the D-15 family
    primitive; proper-noun accents like São/Sao still join). Returns
    {secoes company EXACT string -> (start_date, end_date | None)} for every
    generated entry that matched. Unmatched entries are simply ABSENT: the
    render leaves them dateless and the gate skips ONLY the date sub-check —
    no invented dates, ever (Open Question 1 resolution). Pure function: no
    I/O, no browser import — importable from anywhere.
    """
    dates_by_folded_company = {
        _fold(exp.company.strip()): (exp.start_date, exp.end_date)
        for exp in perfil.experiences
    }
    joined: dict[str, tuple[str, str | None]] = {}
    for exp in secoes.experiencias:
        match = dates_by_folded_company.get(_fold(exp.company.strip()))
        if match is not None:
            joined[exp.company] = match
    return joined


def _tlang(text_map: LocalizedText | None, idioma: str) -> str:
    """tLang convention (ResumeResult.tsx:32-38): EN runs prefer `en` falling
    back to the pt-BR base (schema-guaranteed); PT runs take pt-BR first."""
    if not text_map:
        return ""
    if idioma == "en":
        return text_map.get("en") or text_map.get("pt-BR") or next(
            (value for value in text_map.values() if value), ""
        )
    return text_map.get("pt-BR") or next((value for value in text_map.values() if value), "")


# --- One traversal: structured plain-string content --------------------------


@dataclass
class _Block:
    """One rendered line: `h3` entry title, `meta` muted detail (dates,
    technologies), `p` paragraph, `li` bullet. Text stays PLAIN (unescaped)
    until render time."""

    kind: str
    text: str


@dataclass
class _Section:
    key: str
    blocks: list[_Block]


def _contact_line(perfil) -> str:
    """ResumeResult contact convention (lines 141-148): truthy parts, ' · '-joined."""
    parts = [
        perfil.contact.email,
        perfil.contact.location,
        perfil.contact.phone,
        perfil.contact.linkedin,
    ]
    return CONTACT_SEPARATOR.join(part for part in parts if part)


def _cert_line(cert) -> str:
    """ResumeResult certifications convention: name — issuer (year)."""
    line = cert.name
    if cert.issuer:
        line += f"{EM_DASH_SEPARATOR}{cert.issuer}"
    if cert.year:
        line += f" ({cert.year})"
    return line


def _impact_line(impact, idioma: str) -> str:
    """ResumeResult ImpactBullets convention: action — metric (context)."""
    line = f"{_tlang(impact.action, idioma)}{EM_DASH_SEPARATOR}{_tlang(impact.metric, idioma)}"
    context = _tlang(impact.context, idioma)
    return f"{line} ({context})" if context else line


def _sections_content(perfil, secoes, datas_por_empresa: dict[str, tuple[str, str | None]], idioma: str) -> list[_Section]:
    """The D-05 montage as plain strings, in render order — THE single
    traversal consumed by both build_resume_html and iter_rendered_strings.

    Generated sections (resumo/experiencias/habilidades) always render (the
    backend envelope is all-or-nothing); passthrough sections render only
    when their source list is non-empty (ProfilePreview convention).
    """
    sections: list[_Section] = []

    # resumo (gerado)
    sections.append(_Section("resumo", [_Block("p", secoes.resumo)]))

    # experiencias (gerado) — company · title, date line when joined, bullets
    exp_blocks: list[_Block] = []
    for exp in secoes.experiencias:
        exp_blocks.append(_Block("h3", f"{exp.company}{CONTACT_SEPARATOR}{exp.title}"))
        dates = datas_por_empresa.get(exp.company)
        if dates is not None:
            exp_blocks.append(_Block("meta", format_date_range(dates[0], dates[1])))
        exp_blocks.extend(_Block("li", bullet) for bullet in exp.bullets)
    sections.append(_Section("experiencias", exp_blocks))

    # formacao (perfil) — degree · institution + raw date range
    if perfil.education:
        blocks = []
        for entry in perfil.education:
            blocks.append(
                _Block("h3", f"{entry.degree}{CONTACT_SEPARATOR}{entry.institution}")
            )
            if entry.start_date or entry.end_date:
                blocks.append(
                    _Block("meta", format_date_range(entry.start_date or "", entry.end_date))
                )
        sections.append(_Section("formacao", blocks))

    # habilidades (gerado)
    sections.append(
        _Section("habilidades", [_Block("p", SKILLS_SEPARATOR.join(secoes.habilidades))])
    )

    # certificacoes (perfil)
    if perfil.certifications:
        sections.append(
            _Section(
                "certificacoes",
                [_Block("p", _cert_line(cert)) for cert in perfil.certifications],
            )
        )

    # idiomas (perfil) — name — level
    if perfil.languages:
        sections.append(
            _Section(
                "idiomas",
                [
                    _Block("p", f"{entry.name}{EM_DASH_SEPARATOR}{entry.level}")
                    for entry in perfil.languages
                ],
            )
        )

    # projetos (perfil) — name, run-language description, technologies, impacts
    if perfil.projects:
        blocks: list[_Block] = []
        for project in perfil.projects:
            blocks.append(_Block("h3", project.name))
            blocks.append(_Block("p", _tlang(project.description, idioma)))
            if project.technologies:
                blocks.append(
                    _Block("meta", CONTACT_SEPARATOR.join(project.technologies))
                )
            blocks.extend(
                _Block("li", _impact_line(impact, idioma)) for impact in project.impacts
            )
        sections.append(_Section("projetos", blocks))

    return sections


def rendered_section_keys(
    perfil,
    secoes,
    datas_por_empresa: dict[str, tuple[str, str | None]],
    idioma: str,
) -> tuple[str, ...]:
    """The section keys _sections_content ACTUALLY renders, in render order —
    the template as the single source of truth for the gate's heading
    expectations (CR-01): generated sections always render; passthrough
    sections render only when their source list is non-empty
    (ProfilePreview convention). The export route derives ExpectedDoc.headings
    from THIS same traversal (app.routes.export._expected_doc), so a profile
    with an empty passthrough section can never have that heading demanded of
    its PDF. Same traversal as build_resume_html → template and gate cannot
    drift (D-03)."""
    return tuple(
        section.key
        for section in _sections_content(perfil, secoes, datas_por_empresa, idioma)
    )


def iter_rendered_strings(perfil, secoes, datas_por_empresa: dict[str, tuple[str, str | None]], idioma: str) -> list[str]:
    """Every plain string the template interpolates — header, heading labels
    and all section content, in render order. This list IS the gate's
    accent-integrity universe (check 4): exhaustive over resume-size content,
    never sampled. Same traversal as build_resume_html → no drift."""
    strings = [perfil.name, _contact_line(perfil)]
    labels = HEADINGS[idioma]
    for section in _sections_content(perfil, secoes, datas_por_empresa, idioma):
        strings.append(labels[section.key])
        strings.extend(block.text for block in section.blocks)
    return [text for text in strings if text]


# --- Rendering (escaping happens ONLY here, at the last moment) --------------


def _render_blocks(blocks: list[_Block]) -> str:
    """Blocks → HTML. An `h3` opens an <article>; `li` runs group into <ul>."""
    parts: list[str] = []
    open_article = False
    open_ul = False
    for block in blocks:
        if block.kind == "h3":
            if open_ul:
                parts.append("</ul>")
                open_ul = False
            if open_article:
                parts.append("</article>")
            parts.append(f"<article><h3>{esc(block.text)}</h3>")
            open_article = True
        elif block.kind == "li":
            if not open_ul:
                parts.append("<ul>")
                open_ul = True
            parts.append(f"<li>{esc(block.text)}</li>")
        else:  # "p" | "meta"
            if open_ul:
                parts.append("</ul>")
                open_ul = False
            css_class = ' class="meta"' if block.kind == "meta" else ""
            parts.append(f"<p{css_class}>{esc(block.text)}</p>")
    if open_ul:
        parts.append("</ul>")
    if open_article:
        parts.append("</article>")
    return "".join(parts)


def build_resume_html(
    perfil,
    secoes,
    datas_por_empresa: dict[str, tuple[str, str | None]],
    idioma: str,
) -> str:
    """Render the D-05 montage to a complete HTML document.

    perfil: app.profile.models.Profile. secoes: object carrying the three
    generated sections — `resumo: str`, `experiencias:
    list[ExperienciaGerada]`, `habilidades: list[str]` (the strict request
    model lands in plan 04-02). datas_por_empresa: join_experience_dates
    output. idioma: "pt-BR" | "en" — picks the HEADINGS map.

    Pure: same inputs → same HTML string, no I/O, no clock, no engine calls.
    """
    labels = HEADINGS[idioma]
    contact = _contact_line(perfil)

    parts = [
        "<!DOCTYPE html>",
        f'<html lang="{esc(idioma)}">',
        '<head><meta charset="utf-8">',
        f"<title>{esc(perfil.name)}</title>",
        f"<style>{_CSS}</style></head>",
        "<body>",
        f"<h1>{esc(perfil.name)}</h1>",
    ]
    if contact:
        parts.append(f'<p class="contact">{esc(contact)}</p>')

    for section in _sections_content(perfil, secoes, datas_por_empresa, idioma):
        parts.append(
            f'<section><h2>{esc(labels[section.key])}</h2>{_render_blocks(section.blocks)}</section>'
        )

    parts.append("</body></html>")
    return "".join(parts)
