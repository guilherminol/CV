# -*- coding: utf-8 -*-
"""Render the tailored CV markdown master to an ATS-safe PDF (ReportLab).

Re-run after every edit to cv-forward-deployed-ai-engineer-en.md:
    python render_cv_pdf.py
"""
import re
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
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

# ── Fonts (Windows Times New Roman) ──
FONTS = "C:/Windows/Fonts"
pdfmetrics.registerFont(TTFont("TimesNewRoman", f"{FONTS}/times.ttf"))
pdfmetrics.registerFont(TTFont("TimesNewRoman-Bold", f"{FONTS}/timesbd.ttf"))
pdfmetrics.registerFont(TTFont("TimesNewRoman-Italic", f"{FONTS}/timesi.ttf"))
pdfmetrics.registerFont(TTFont("TimesNewRoman-BoldItalic", f"{FONTS}/timesbi.ttf"))
registerFontFamily(
    "TimesNewRoman",
    normal="TimesNewRoman",
    bold="TimesNewRoman-Bold",
    italic="TimesNewRoman-Italic",
    boldItalic="TimesNewRoman-BoldItalic",
)

# ── Palette (from pdf.py palette.cascade --mode minimal) ──
HEADER_FILL = colors.HexColor("#445c68")   # M tier — section titles + rules
TEXT_PRIMARY = colors.HexColor("#181a1b")
TEXT_MUTED = colors.HexColor("#6d7376")    # darkened from #848a8d for print contrast

name_style = ParagraphStyle(
    "ResumeName", fontName="TimesNewRoman", fontSize=24, leading=28,
    alignment=TA_CENTER, textColor=TEXT_PRIMARY, spaceAfter=2,
)
contact_style = ParagraphStyle(
    "ResumeContact", fontName="TimesNewRoman", fontSize=10, leading=13.5,
    alignment=TA_CENTER, textColor=TEXT_MUTED, spaceAfter=0,
)
section_title_style = ParagraphStyle(
    "ResumeSectionTitle", fontName="TimesNewRoman", fontSize=13.5, leading=17,
    spaceBefore=0, spaceAfter=0, textColor=HEADER_FILL,
)
body_style = ParagraphStyle(
    "ResumeBody", fontName="TimesNewRoman", fontSize=11, leading=15.2,
    textColor=TEXT_PRIMARY, spaceBefore=2.5, spaceAfter=2.5,
    allowWidows=0, allowOrphans=0,
)
bullet_style = ParagraphStyle(
    "ResumeBullet", fontName="TimesNewRoman", fontSize=11, leading=14.8,
    leftIndent=14, bulletIndent=2, textColor=TEXT_PRIMARY,
    spaceBefore=2.5, spaceAfter=2.5, allowWidows=0, allowOrphans=0,
)

LABEL_RE = re.compile(r"^\*\*[^*]+:\*\*$")


def esc(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def section_header(title: str):
    return [
        CondPageBreak(4 * cm),
        Spacer(1, 14),
        KeepTogether([
            Paragraph(f"<b>{esc(title)}</b>", section_title_style),
            HRFlowable(width="100%", thickness=0.8, color=HEADER_FILL,
                       spaceBefore=3, spaceAfter=7),
        ]),
    ]


def main():
    with open(MD_PATH, encoding="utf-8") as f:
        md_text = f.read()

    story = []
    in_contact = False
    contact_buf = []
    pending_label = None  # standalone **Label:** line awaiting its first content

    def flush(block):
        nonlocal pending_label
        if pending_label is not None:
            story.append(KeepTogether([pending_label, block]))
            pending_label = None
        else:
            story.append(block)

    for raw in md_text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("# "):
            story.append(Paragraph(esc(line[2:]), name_style))
            story.append(Spacer(1, 4))
            in_contact = True
        elif line.startswith("## "):
            if contact_buf:
                for c in contact_buf:
                    story.append(Paragraph(esc(c), contact_style))
                contact_buf = []
            in_contact = False
            story.extend(section_header(line[3:]))
        elif line.startswith("- "):
            flush(Paragraph("• " + esc(line[2:]), bullet_style))
        elif LABEL_RE.match(line.strip()) and not in_contact:
            pending_label = Paragraph(esc(line), body_style)
        else:
            if in_contact:
                contact_buf.append(line)
            else:
                flush(Paragraph(esc(line), body_style))
    if pending_label is not None:
        story.append(pending_label)

    doc = BaseDocTemplate(
        PDF_PATH, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
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
    print(f"OK {PDF_PATH}")


if __name__ == "__main__":
    sys.exit(main())
