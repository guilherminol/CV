"""Export print template (D-03/D-05) — pure HTML builder: no I/O, no template engine.

build_resume_html mirrors the D-05 montage the result screen shows
(ResumeResult.tsx:139-255): name/contact header, then sections in PREVIEW
order — resumo (gerado), experiencias (gerado), formacao (perfil),
habilidades (gerado), certificacoes/idiomas/projetos (perfil); zero-entry
sections stay hidden for ALL sections (ProfilePreview convention; quick
task 261006-oy9 extended the guard to the generated sections so an export
selection can empty them — the min_length=1 envelope floors keep them
non-empty when no selection travels).

Single source of truth (D-03): HEADINGS maps every section key to its
run-language label — gate.py's heading-order check and (plan 04-02) the
selfcheck ordem rows assert against THIS map, never a copy. A2 (Task 0
verdict, confirmed 2026-09-27): ALL 7 headings localize to the run language —
an EN run renders Summary/Experience/Education/Skills/... — a
presentation-only divergence from the in-app PT-BR passthrough-label
convention; content itself still travels verbatim (D-10).

Dates on generated experiences (research Open Questions 1+3):
join_experience_dates joins perfil.experiences date ranges onto
secoes.experiencias — one result element PER generated entry, in order.
Matching is by folded company, then POSITIONAL within the company bucket
(WR-01: two stints at one employer keep their own dates — the old
dict-by-company shape collapsed both entries onto the last stored range).
Matched entries render `format_date_range(start, end, idioma)` — RAW stored
strings, "start – end" or "start – atual/present" per run language (the
dateRange() convention, no locale formatting). Unmatched (or exhausted-bucket)
entries render dateless — no invented dates, ever.

Safety (V5.3, T-04-01): every data string passes through esc() —
html.escape(quote=True) — so profile/LLM text can never inject markup into
the rendered document (server-side analogue of the JSX-text-children
convention). Pure functions: same inputs → same HTML.

Engine-agnostic CSS (D-01/D-02 reversibility): block layout only — no
flex/grid/floats — declaring BOTH break-inside properties (WeasyPrint
reliably honors the legacy page-break-inside). Page-break atomicity lives
on the ENTRY (`article`), never on the whole `section`: a section longer
than one page must flow across the page boundary — section-level avoid
pushes the entire block to the next page and strands a near-empty first
page (the void-page bug). `h2` declares break-after: avoid so a heading
never orphans at a page bottom. Headings are written in final case; NO
text-transform anywhere (Pitfall 3: Chromium bakes transformed glyphs
into the PDF text layer).

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
PRESENT_LABELS: dict[str, str] = {"pt-BR": "atual", "en": "present"}  # run-language open-range word
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

# Escopo de projetos (schema Project.scope): rótulo de grupo localizado por
# run language — profissional (in-company) e pessoal nunca dividem a mesma
# lista. Ordem fixa: profissional primeiro.
SCOPE_LABELS = {
    "profissional": {"pt-BR": "Projetos profissionais", "en": "Professional projects"},
    "pessoal": {"pt-BR": "Projetos pessoais", "en": "Personal projects"},
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
h2 { font-size: 11.5pt; margin: 14pt 0 4pt 0; border-bottom: 0.5pt solid #999999; padding-bottom: 2pt; break-after: avoid; page-break-after: avoid; }
h3 { font-size: 10.5pt; margin: 8pt 0 2pt 0; }
h4 { font-size: 9.5pt; margin: 10pt 0 2pt 0; color: #444444; }
p { margin: 2pt 0; }
ul { margin: 2pt 0; padding-left: 14pt; }
li { margin: 1pt 0; }
article { break-inside: avoid; page-break-inside: avoid; }
.contact { color: #444444; }
.meta { color: #555555; }
"""


def esc(text: str) -> str:
    """Escape EVERY interpolated data string — no exceptions (V5.3, T-04-01)."""
    return html.escape(text, quote=True)


def format_date_range(start: str, end: str | None, idioma: str = "pt-BR") -> str:
    """dateRange() convention (ResumeResult.tsx:41-43): raw stored strings;
    open ranges show the run-language word ('atual'/'present'). No locale
    formatting (Open Question 3). The default keeps the PT-BR base-language
    convention for callers without a run language in scope."""
    present = PRESENT_LABELS.get(idioma, PRESENT_LABELS["pt-BR"])
    return f"{start}{DATE_SEPARATOR}{end}" if end else f"{start}{DATE_SEPARATOR}{present}"


def join_experience_dates(
    perfil, secoes
) -> list[tuple[str, str | None] | None]:
    """Join perfil.experiences date ranges onto the generated entries — one
    result element PER secoes.experiencias entry, in order.

    Match key: strip + coverage._fold (casefold + NFKD — the D-15 family
    primitive; proper-noun accents like São/Sao still join). Stored ranges
    are grouped per folded company, then consumed POSITIONALLY (WR-01): the
    first generated entry for a company takes the profile's first stored
    range for that company, the second takes the second — two stints at one
    employer (career progression) each keep their own dates; the previous
    dict-by-company shape collapsed both entries onto the LAST stored range,
    printing factually wrong dates on a sendable document. An entry whose
    company matches nothing — or whose bucket is exhausted — is None: the
    render leaves it dateless and the gate skips ONLY the date sub-check —
    no invented dates, ever (Open Question 1 resolution). Pure function: no
    I/O, no browser import — importable from anywhere.
    """
    ranges_by_folded_company: dict[str, list[tuple[str, str | None]]] = {}
    for exp in perfil.experiences:
        ranges_by_folded_company.setdefault(_fold(exp.company.strip()), []).append(
            (exp.start_date, exp.end_date)
        )
    joined: list[tuple[str, str | None] | None] = []
    for exp in secoes.experiencias:
        bucket = ranges_by_folded_company.get(_fold(exp.company.strip()))
        joined.append(bucket.pop(0) if bucket else None)
    return joined


def _tlang(text_map: LocalizedText | str | None, idioma: str) -> str:
    """tLang convention (ResumeResult.tsx:32-38): EN runs prefer `en` falling
    back to the pt-BR base (schema-guaranteed); PT runs take pt-BR first.
    Plain-str fields (schema `str | LocalizedText` unions) pass through —
    a brand name with no translation is valid content, never a crash."""
    if not text_map:
        return ""
    if isinstance(text_map, str):
        return text_map
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


def _contact_line(perfil, idioma: str) -> str:
    """ResumeResult contact convention (lines 141-148): truthy parts, ' · '-joined.
    Location and phone are localized (run language); email/LinkedIn are neutral."""
    parts = [
        perfil.contact.email,
        _tlang(perfil.contact.location, idioma) or None,
        _tlang(perfil.contact.phone, idioma) or None,
        perfil.contact.linkedin,
    ]
    return CONTACT_SEPARATOR.join(part for part in parts if part)


def _cert_line(cert, idioma: str) -> str:
    """ResumeResult certifications convention: name — issuer (year). The
    issuer is localized (it may carry the certificate's nature per language)."""
    line = cert.name
    issuer = _tlang(cert.issuer, idioma)
    if issuer:
        line += f"{EM_DASH_SEPARATOR}{issuer}"
    if cert.year:
        line += f" ({cert.year})"
    return line


def _impact_line(impact, idioma: str) -> str:
    """ResumeResult ImpactBullets convention: action — metric (context)."""
    line = f"{_tlang(impact.action, idioma)}{EM_DASH_SEPARATOR}{_tlang(impact.metric, idioma)}"
    context = _tlang(impact.context, idioma)
    return f"{line} ({context})" if context else line


def _sections_content(
    perfil,
    secoes,
    datas_por_experiencia: list[tuple[str, str | None] | None],
    idioma: str,
) -> list[_Section]:
    """The D-05 montage as plain strings, in render order — THE single
    traversal consumed by both build_resume_html and iter_rendered_strings.

    datas_por_experiencia: join_experience_dates output — one element per
    generated experience entry, in order (None = dateless entry).

    Zero-entry hiding covers ALL sections (quick task 261006-oy9): generated
    sections (resumo/experiencias/habilidades) render only when their source
    is non-empty, and passthrough sections only when their source list is
    non-empty (ProfilePreview convention). With no export selection this
    changes NOTHING — the strict envelope's min_length=1 floors guarantee
    the three generated sources non-empty, so they always render today. The
    export route's selection filter (app.routes.export._aplicar_selecao) can
    empty them, and because rendered_section_keys/iter_rendered_strings
    traverse THIS same function, the gate's heading expectations adapt
    automatically (CR-01 invariant intact — template and gate cannot drift).
    """
    sections: list[_Section] = []

    # resumo (gerado) — hidden when the selection emptied it (empty string)
    if secoes.resumo:
        sections.append(_Section("resumo", [_Block("p", secoes.resumo)]))

    # experiencias (gerado) — company · title, date line when joined, bullets;
    # hidden when the selection left zero entries (empty block list)
    exp_blocks: list[_Block] = []
    for idx, exp in enumerate(secoes.experiencias):
        exp_blocks.append(_Block("h3", f"{exp.company}{CONTACT_SEPARATOR}{exp.title}"))
        dates = datas_por_experiencia[idx] if idx < len(datas_por_experiencia) else None
        if dates is not None:
            exp_blocks.append(_Block("meta", format_date_range(dates[0], dates[1], idioma)))
        exp_blocks.extend(_Block("li", bullet) for bullet in exp.bullets)
    if exp_blocks:
        sections.append(_Section("experiencias", exp_blocks))

    # formacao (perfil) — degree · institution + raw date range
    if perfil.education:
        blocks = []
        for entry in perfil.education:
            blocks.append(
                _Block(
                    "h3",
                    f"{_tlang(entry.degree, idioma)}{CONTACT_SEPARATOR}{entry.institution}",
                )
            )
            if entry.start_date or entry.end_date:
                blocks.append(
                    _Block(
                        "meta",
                        format_date_range(entry.start_date or "", entry.end_date, idioma),
                    )
                )
        sections.append(_Section("formacao", blocks))

    # habilidades (gerado) — hidden when the selection emptied it
    if secoes.habilidades:
        sections.append(
            _Section("habilidades", [_Block("p", SKILLS_SEPARATOR.join(secoes.habilidades))])
        )

    # certificacoes (perfil)
    if perfil.certifications:
        sections.append(
            _Section(
                "certificacoes",
                [_Block("p", _cert_line(cert, idioma)) for cert in perfil.certifications],
            )
        )

    # idiomas (perfil) — name — level
    if perfil.languages:
        sections.append(
            _Section(
                "idiomas",
                [
                    _Block(
                        "p",
                        f"{_tlang(entry.name, idioma)}{EM_DASH_SEPARATOR}{_tlang(entry.level, idioma)}",
                    )
                    for entry in perfil.languages
                ],
            )
        )

    # projetos (perfil) — agrupados por escopo (profissional primeiro), com
    # rótulo de grupo localizado: empregador e projeto pessoal nunca se
    # misturam na mesma lista (o recrutador lê cada um no contexto certo).
    # name resolve por _tlang (str brand OU mapa localizado).
    if perfil.projects:
        ordered: dict[str, list] = {"profissional": [], "pessoal": []}
        for project in perfil.projects:
            ordered[project.scope].append(project)
        blocks: list[_Block] = []
        for scope_key in ("profissional", "pessoal"):
            group = ordered[scope_key]
            if not group:
                continue
            blocks.append(_Block("h4", _tlang(SCOPE_LABELS[scope_key], idioma)))
            for project in group:
                blocks.append(_Block("h3", _tlang(project.name, idioma)))
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
    datas_por_experiencia: list[tuple[str, str | None] | None],
    idioma: str,
) -> tuple[str, ...]:
    """The section keys _sections_content ACTUALLY renders, in render order —
    the template as the single source of truth for the gate's heading
    expectations (CR-01): generated sections render only when their source is
    non-empty (an export selection can empty them), passthrough sections only
    when their source list is non-empty (ProfilePreview convention). The
    export route derives ExpectedDoc.headings from THIS same traversal
    (app.routes.export._expected_doc), so a section emptied by the selection —
    or an empty passthrough profile section — can never have its heading
    demanded of the PDF. Same traversal as build_resume_html → template and
    gate cannot drift (D-03)."""
    return tuple(
        section.key
        for section in _sections_content(perfil, secoes, datas_por_experiencia, idioma)
    )


def iter_rendered_strings(
    perfil,
    secoes,
    datas_por_experiencia: list[tuple[str, str | None] | None],
    idioma: str,
) -> list[str]:
    """Every plain string the template interpolates — header, heading labels
    and all section content, in render order. This list IS the gate's
    accent-integrity universe (check 4): exhaustive over resume-size content,
    never sampled. Same traversal as build_resume_html → no drift."""
    strings = [perfil.name, _contact_line(perfil, idioma)]
    labels = HEADINGS[idioma]
    for section in _sections_content(perfil, secoes, datas_por_experiencia, idioma):
        strings.append(labels[section.key])
        strings.extend(block.text for block in section.blocks)
    return [text for text in strings if text]


# --- Rendering (escaping happens ONLY here, at the last moment) --------------


def _render_blocks(blocks: list[_Block]) -> str:
    """Blocks → HTML. An `h3` opens an <article>; `li` runs group into <ul>;
    `h4` is a group label that closes the running article without opening one."""
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
        elif block.kind == "h4":
            if open_ul:
                parts.append("</ul>")
                open_ul = False
            if open_article:
                parts.append("</article>")
                open_article = False
            parts.append(f"<h4>{esc(block.text)}</h4>")
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
    datas_por_experiencia: list[tuple[str, str | None] | None],
    idioma: str,
) -> str:
    """Render the D-05 montage to a complete HTML document.

    perfil: app.profile.models.Profile. secoes: object carrying the three
    generated sections — `resumo: str`, `experiencias:
    list[ExperienciaGerada]`, `habilidades: list[str]` (the strict request
    model lands in plan 04-02). datas_por_experiencia: join_experience_dates
    output — one element per generated experience entry, in order (None =
    dateless). idioma: "pt-BR" | "en" — picks the HEADINGS map.

    Pure: same inputs → same HTML string, no I/O, no clock, no engine calls.
    """
    labels = HEADINGS[idioma]
    contact = _contact_line(perfil, idioma)

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

    for section in _sections_content(perfil, secoes, datas_por_experiencia, idioma):
        parts.append(
            f'<section><h2>{esc(labels[section.key])}</h2>{_render_blocks(section.blocks)}</section>'
        )

    parts.append("</body></html>")
    return "".join(parts)
