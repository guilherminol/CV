# -*- coding: utf-8 -*-
"""Render the tailored CV markdown master to an ATS-safe PDF (ReportLab).

Visual design replicates the app's export CSS (backend/app/export/render.py
_CSS): Segoe UI 10.5pt body in #111111 on A4 with 1.6cm margins, h1 20pt
left-aligned, h2 11.5pt bold with a 0.5pt #999999 bottom rule, h3 10.5pt bold
entry headings, h4 9.5pt #444444 group labels, gray (#555555) meta lines,
#444444 contact line. Structure mirrors the app's D-05 montage: Summary /
Experience / Education / Core Skills / Certifications / Languages / Projects.

Markdown vocabulary:
    #  name            ##  section title     ###  entry heading
    #### group label   >   meta line (dates, tech)   -  bullet
    **Label:** standalone line sticks to its first content block

Re-run after every edit to cv-forward-deployed-ai-engineer-en.md:
    python render_cv_pdf.py
"""
import re
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, HRFlowable,
    KeepTogether, CondPageBreak,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

HERE = __file__.replace("\\", "/").rsplit("/", 1)[0]
MD_PATH = f"{HERE}/cv-forward-deployed-ai-engineer-en.md"
PDF_PATH = f"{HERE}/Guilhermino-Lucas-CV-Forward-Deployed-AI-Engineer.pdf"
TMP_PATH = PDF_PATH + ".building.pdf"

# ── Fonts (Windows Segoe UI — the app's export font stack) ──
FONTS = "C:/Windows/Fonts"
pdfmetrics.registerFont(TTFont("SegoeUI", f"{FONTS}/segoeui.ttf"))
pdfmetrics.registerFont(TTFont("SegoeUI-Bold", f"{FONTS}/segoeuib.ttf"))
pdfmetrics.registerFont(TTFont("SegoeUI-Italic", f"{FONTS}/segoeuii.ttf"))
pdfmetrics.registerFont(TTFont("SegoeUI-BoldItalic", f"{FONTS}/segoeuiz.ttf"))
registerFontFamily(
    "SegoeUI",
    normal="SegoeUI",
    bold="SegoeUI-Bold",
    italic="SegoeUI-Italic",
    boldItalic="SegoeUI-BoldItalic",
)

# ── Palette — the app's _CSS values, verbatim ──
BODY = colors.HexColor("#111111")     # body text
CONTACT = colors.HexColor("#444444")  # .contact / h4
META = colors.HexColor("#555555")     # .meta (dates, tech lines)
RULE = colors.HexColor("#999999")     # h2 border-bottom

# browser-normal line height for Segoe UI ≈ 1.36em; 14 balances page fill
LEAD = 12.6

name_style = ParagraphStyle(
    "ResumeName", fontName="SegoeUI", fontSize=20, leading=26,
    alignment=TA_LEFT, textColor=BODY, spaceBefore=0, spaceAfter=2,
)
contact_style = ParagraphStyle(
    "ResumeContact", fontName="SegoeUI", fontSize=10, leading=13,
    alignment=TA_LEFT, textColor=CONTACT, spaceBefore=0, spaceAfter=4,
)
section_title_style = ParagraphStyle(
    "ResumeSectionTitle", fontName="SegoeUI", fontSize=11.5, leading=15,
    spaceBefore=0, spaceAfter=0, textColor=BODY,
)
entry_title_style = ParagraphStyle(
    "ResumeEntryTitle", fontName="SegoeUI", fontSize=10.5, leading=LEAD,
    textColor=BODY, spaceBefore=5, spaceAfter=2,
    allowWidows=0, allowOrphans=0,
)
group_label_style = ParagraphStyle(
    "ResumeGroupLabel", fontName="SegoeUI", fontSize=9.5, leading=13,
    textColor=CONTACT, spaceBefore=10, spaceAfter=2,
)
meta_style = ParagraphStyle(
    "ResumeMeta", fontName="SegoeUI", fontSize=10.5, leading=LEAD,
    textColor=META, spaceBefore=0, spaceAfter=2,
    allowWidows=0, allowOrphans=0,
)
body_style = ParagraphStyle(
    "ResumeBody", fontName="SegoeUI", fontSize=10.5, leading=LEAD,
    textColor=BODY, spaceBefore=2, spaceAfter=2,
    allowWidows=0, allowOrphans=0,
)
bullet_style = ParagraphStyle(
    "ResumeBullet", fontName="SegoeUI", fontSize=10.5, leading=LEAD,
    leftIndent=14, bulletIndent=2, textColor=BODY,
    spaceBefore=1, spaceAfter=1, allowWidows=0, allowOrphans=0,
)

LABEL_RE = re.compile(r"^\*\*[^*]+:\*\*$")


def esc(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def section_header(title: str):
    """h2 + border-bottom (0.5pt #999999, 2pt padding), margin 14pt/4pt."""
    return [
        CondPageBreak(3.5 * cm),
        Spacer(1, 7),
        KeepTogether([
            Paragraph(f"<b>{esc(title)}</b>", section_title_style),
            Spacer(1, 2),
            HRFlowable(width="100%", thickness=0.5, color=RULE,
                       spaceBefore=0, spaceAfter=4),
        ]),
    ]


def main():
    with open(MD_PATH, encoding="utf-8") as f:
        md_text = f.read()

    story = []
    in_contact = False
    contact_buf = []
    pending_blocks = []   # entry heading (+ optional meta line) awaiting first content
    pending_label = None  # standalone **Label:** line awaiting its first content

    def flush(block):
        nonlocal pending_blocks, pending_label
        chain = pending_blocks + ([pending_label] if pending_label else []) + [block]
        pending_blocks = []
        pending_label = None
        story.append(KeepTogether(chain) if len(chain) > 1 else chain[0])

    for raw in md_text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("#### "):
            if pending_blocks:
                story.extend(pending_blocks)
                pending_blocks = []
            pending_label = None
            story.append(Paragraph(esc(line[5:]), group_label_style))
        elif line.startswith("### "):
            pending_blocks = [Paragraph("<b>" + esc(line[4:]) + "</b>", entry_title_style)]
        elif line.startswith("## "):
            if pending_blocks:
                story.extend(pending_blocks)
                pending_blocks = []
            pending_label = None
            if contact_buf:
                for c in contact_buf:
                    story.append(Paragraph(esc(c), contact_style))
                contact_buf = []
            in_contact = False
            story.extend(section_header(line[3:]))
        elif line.startswith("# "):
            # headline: name at 20pt, vacancy title as a smaller muted suffix
            head = esc(line[2:])
            if "|" in head:
                name, _, suffix = head.partition("|")
                head = f'{name}<font size="13.5" color="#555555"> | {suffix}</font>'
            story.append(Paragraph(head, name_style))
            in_contact = True
        elif line.startswith("> "):
            meta = Paragraph(esc(line[2:]), meta_style)
            if pending_blocks:
                pending_blocks.append(meta)
            else:
                flush(meta)
        elif line.startswith("- "):
            flush(Paragraph("• " + esc(line[2:]), bullet_style))
        elif LABEL_RE.match(line.strip()) and not in_contact:
            pending_label = Paragraph(esc(line), body_style)
        else:
            if in_contact:
                contact_buf.append(line)
            else:
                flush(Paragraph(esc(line), body_style))

    story.extend(pending_blocks)
    if pending_label is not None:
        story.append(pending_label)

    doc = BaseDocTemplate(
        TMP_PATH, pagesize=A4,
        leftMargin=1.6 * cm, rightMargin=1.6 * cm,
        topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        title="Guilhermino Lucas — CV — Forward Deployed AI Engineer",
        author="Guilhermino Lucas",
        subject="Tailored CV — Forward Deployed AI Engineer",
        creator="ReportLab",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                  id="main", leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="page", frames=[frame])])
    doc.build(story)
    import os, time
    for attempt in range(5):
        try:
            os.replace(TMP_PATH, PDF_PATH)
            break
        except OSError:
            time.sleep(1.5)
    else:
        print(f"WARNING: {PDF_PATH} locked; left {TMP_PATH}")
        sys.exit(2)
    print(f"OK {PDF_PATH}")


if __name__ == "__main__":
    sys.exit(main())
