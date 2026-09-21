"""Build the SSAC27 submission PDF from the verified sources.

The portal takes ONE file: title, the four abstract sections, and both
exhibits must live in a single document. This script assembles it from
`paper/abstract.md`, `analysis/output/exhibit1-persistence.png`, and
`analysis/output/exhibit2-taxonomy.md` — nothing is hand-transcribed, so
the typeset table cannot drift from the oracle-verified outputs.

Hard-fails if the abstract (title + body) reaches 500 words or if any
author-identifying string appears in the assembled text (blind review).

  python paper/build_submission.py   -> paper/submission.pdf
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PAPER = Path(__file__).resolve().parent
OUTPUT = PAPER.parent / "analysis" / "output"

WORD_LIMIT = 500  # fewer than 500 words, title included
BLIND_REVIEW_STRINGS = ("jayson", "jorgensen", "jayjorg", "nba-analytics",
                        "readinghorizons")

INK = colors.HexColor("#0b0b0b")
INK_SECONDARY = colors.HexColor("#52514e")
RULE = colors.HexColor("#c3c2b7")
GRID = colors.HexColor("#e1e0d9")


def parse_abstract(path: Path) -> tuple[str, list[tuple[str, str]]]:
    """The H1 title and the (heading, body) pairs, in order."""
    text = path.read_text(encoding="utf-8")
    title_match = re.match(r"#\s+(.+)", text)
    if not title_match:
        raise SystemExit("abstract.md has no H1 title")
    title = title_match.group(1).strip()
    sections = re.findall(r"^##\s+(.+?)\n(.*?)(?=^##\s|\Z)", text,
                          flags=re.M | re.S)
    return title, [(h.strip(), " ".join(b.split())) for h, b in sections]


def parse_taxonomy(path: Path) -> tuple[list[list[str]], str]:
    """The exhibit-2 table rows (header first) and its trailing note."""
    lines = path.read_text(encoding="utf-8").splitlines()
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in lines
        if line.startswith("|") and not set(line) <= set("|-: ")
    ]
    note = next(
        (line.strip() for line in reversed(lines) if line.strip()
         and not line.startswith(("|", "#"))),
        "",
    )
    return rows, note


def count_words(title: str, sections: list[tuple[str, str]]) -> int:
    text = " ".join([title] + [f"{h} {b}" for h, b in sections])
    return len(re.findall(r"\S+", text))


def register_fonts() -> tuple[str, str]:
    """Embed Times New Roman (full Latin glyph set — 'Jokić' needs ć,
    which the base-14 PDF fonts lack); fall back to base Times."""
    fonts_dir = Path("C:/Windows/Fonts")
    faces = {"times.ttf": "TNR", "timesbd.ttf": "TNR-Bold",
             "timesi.ttf": "TNR-Italic", "timesbi.ttf": "TNR-BoldItalic"}
    if not all((fonts_dir / f).exists() for f in faces):
        return "Times-Roman", "Times-Bold"
    for file, name in faces.items():
        pdfmetrics.registerFont(TTFont(name, str(fonts_dir / file)))
    registerFontFamily("TNR", normal="TNR", bold="TNR-Bold",
                       italic="TNR-Italic", boldItalic="TNR-BoldItalic")
    return "TNR", "TNR-Bold"


def main() -> None:
    title, sections = parse_abstract(PAPER / "abstract.md")
    rows, note = parse_taxonomy(OUTPUT / "exhibit2-taxonomy.md")
    fig_path = OUTPUT / "exhibit1-persistence.png"

    words = count_words(title, sections)
    if words >= WORD_LIMIT:
        raise SystemExit(f"abstract is {words} words incl. title; the rule "
                         f"is fewer than {WORD_LIMIT}")

    font, font_bold = register_fonts()
    body_style = ParagraphStyle(
        "body", fontName=font, fontSize=10.5, leading=14,
        alignment=TA_JUSTIFY, textColor=INK, spaceAfter=8,
    )
    title_style = ParagraphStyle(
        "title", parent=body_style, fontName=font_bold, fontSize=14.5,
        leading=18, alignment=0, spaceAfter=14,
    )
    heading_style = ParagraphStyle(
        "heading", parent=body_style, fontName=font_bold, fontSize=11,
        spaceBefore=4, spaceAfter=4,
    )
    caption_style = ParagraphStyle(
        "caption", parent=body_style, fontSize=9, leading=12,
        textColor=INK_SECONDARY, spaceBefore=4, spaceAfter=2,
    )
    cell_style = ParagraphStyle(
        "cell", parent=body_style, fontSize=8.5, leading=11, alignment=0,
        spaceAfter=0,
    )
    cell_right = ParagraphStyle("cellRight", parent=cell_style, alignment=2)
    head_style = ParagraphStyle(
        "head", parent=cell_style, fontName=font_bold,
    )
    head_right = ParagraphStyle("headRight", parent=head_style, alignment=2)

    story: list = [Paragraph(title, title_style)]
    for heading, body in sections:
        story.append(Paragraph(heading, heading_style))
        story.append(Paragraph(body, body_style))

    # Figure 1 — the PNG at text width, aspect preserved.
    text_width = 6.5 * inch
    with PILImage.open(fig_path) as img:
        px_w, px_h = img.size
    story.append(Spacer(1, 10))
    story.append(Image(str(fig_path), width=text_width,
                       height=text_width * px_h / px_w))
    story.append(Paragraph(
        "<b>Figure 1.</b> Channel persistence with the context test: "
        "year-over-year correlation for players who stayed vs changed "
        "teams, against the within-season (split-half) reliability "
        "ceiling. Pooled transitions, 2023-24 … 2025-26.", caption_style))

    # Table 1 — typeset from the committed exhibit, headers spelled out.
    header = ["Channel", "Tier", "League trips (2025-26)",
              "Median /100 FGA (p10–p90)", "Year-over-year r",
              "Split-half reliability"]
    data = [[Paragraph(h, head_style if i < 2 else head_right)
             for i, h in enumerate(header)]]
    for row in rows[1:]:
        cells = [re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", c) for c in row]
        data.append([Paragraph(c, cell_style if i < 2 else cell_right)
                     for i, c in enumerate(cells)])
    table = Table(
        data,
        colWidths=[1.55 * inch, 1.12 * inch, 0.82 * inch, 1.19 * inch,
                   1.00 * inch, 0.82 * inch],
        repeatRows=1,
    )
    table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.9, RULE),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, RULE),
        ("LINEBELOW", (0, -1), (-1, -1), 0.9, RULE),
        ("LINEABOVE", (0, -1), (-1, -1), 0.25, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "<b>Table 1.</b> The trip taxonomy, measured. Volume and rate "
        "columns are 2025-26 (players with ≥300 field-goal attempts); "
        "both stability columns are pooled over 2023-24 … 2025-26.",
        caption_style))
    story.append(table)
    story.append(Paragraph(f"<i>Note.</i> {note}", caption_style))

    assembled = " ".join(
        flowable.text for flowable in story if isinstance(flowable, Paragraph)
    ).lower()
    for needle in BLIND_REVIEW_STRINGS:
        if needle in assembled:
            raise SystemExit(f"blind-review violation: {needle!r} appears "
                             "in the assembled document")

    out_path = PAPER / "submission.pdf"
    doc = SimpleDocTemplate(
        str(out_path), pagesize=letter,
        leftMargin=inch, rightMargin=inch, topMargin=inch,
        bottomMargin=inch, title=title, author="",
    )
    doc.build(story)
    print(f"abstract: {words} words incl. title (< {WORD_LIMIT})")
    print(f"submission -> {out_path}")


if __name__ == "__main__":
    main()
