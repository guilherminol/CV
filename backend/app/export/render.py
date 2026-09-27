"""Export print template (D-03/D-05) — pure HTML builder: no I/O, no template engine.

build_resume_html mirrors the D-05 montage the result screen shows
(ResumeResult.tsx): name/contact header, then sections in PREVIEW order —
resumo (gerado), experiencias (gerado), formacao (perfil), habilidades
(gerado), certificacoes/idiomas/projetos (perfil); zero-entry passthrough
sections stay hidden (ProfilePreview convention).

Single source of truth (D-03): HEADINGS maps every section key to its
run-language label — gate.py's heading-order check and (plan 04-02) the
selfcheck ordem rows assert against THIS map, never a copy. A2 (Task 0
verdict, confirmed 2026-09-27): ALL 7 headings localize to the run language —
an EN run renders Summary/Experience/Education/Skills/... — a
presentation-only divergence from the in-app PT-BR passthrough-label
convention; content itself still travels verbatim (D-10).

Safety (V5.3, T-04-01): every data string passes through esc() —
html.escape(quote=True) — so profile/LLM text can never inject markup into
the rendered document (server-side analogue of the JSX-text-children
convention). The pure-function contract means same inputs → same HTML.

Engine-agnostic CSS (D-01/D-02 reversibility): block layout only — no
flex/grid/floats — declaring BOTH break-inside properties (WeasyPrint
reliably honors the legacy page-break-inside). Headings are written in final
case; NO text-transform anywhere (Pitfall 3: Chromium bakes transformed
glyphs into the PDF text layer).

Tracer scope (this task): the CORE montage — header + resumo + experiencias
+ habilidades. The passthrough sections and the experience-dates rendering
are completed later in this plan (fill-later by design: empty passthrough
sections are legitimately hidden in the montage anyway).
"""

import html

CONTACT_SEPARATOR = " · "  # PREVIEW_CONTACT_SEPARATOR convention (constants/ui.ts)
SKILLS_SEPARATOR = ", "  # ResumeResult renders habilidades.join(', ')
DATE_SEPARATOR = " – "  # dateRange() convention: raw stored strings (Open Question 3)
PRESENT = "atual"  # PREVIEW_PRESENT convention

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
"""


def esc(text: str) -> str:
    """Escape EVERY interpolated data string — no exceptions (V5.3, T-04-01)."""
    return html.escape(text, quote=True)


def _contact_line(perfil) -> str:
    """ResumeResult contact convention (lines 141-148): truthy parts, ' · '-joined."""
    parts = [
        perfil.contact.email,
        perfil.contact.location,
        perfil.contact.phone,
        perfil.contact.linkedin,
    ]
    return CONTACT_SEPARATOR.join(part for part in parts if part)


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
    model lands in plan 04-02). datas_por_empresa: {company -> (start,
    end|None)} raw stored date strings from join_experience_dates (Task 2 of
    this plan renders them). idioma: "pt-BR" | "en" — picks the HEADINGS map.

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

    # resumo (gerado)
    parts.append(
        f'<section><h2>{esc(labels["resumo"])}</h2>'
        f"<p>{esc(secoes.resumo)}</p></section>"
    )

    # experiencias (gerado) — company · title line + bullets (date line: Task 2)
    entries = []
    for exp in secoes.experiencias:
        bullets = "".join(f"<li>{esc(bullet)}</li>" for bullet in exp.bullets)
        entries.append(
            f"<article><h3>{esc(exp.company)}{CONTACT_SEPARATOR}{esc(exp.title)}</h3>"
            f"<ul>{bullets}</ul></article>"
        )
    parts.append(
        f'<section><h2>{esc(labels["experiencias"])}</h2>{"".join(entries)}</section>'
    )

    # habilidades (gerado)
    parts.append(
        f'<section><h2>{esc(labels["habilidades"])}</h2>'
        f"<p>{esc(SKILLS_SEPARATOR.join(secoes.habilidades))}</p></section>"
    )

    parts.append("</body></html>")
    return "".join(parts)
