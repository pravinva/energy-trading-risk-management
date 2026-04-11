#!/usr/bin/env python3
"""
Generate market-specific persona day-in-the-life PDFs from markdown docs.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


MARKET_DOCS = [
    ("APEX_NEM_PERSONA_DAY_IN_LIFE.md", "APEX_NEM_PERSONA_DAY_IN_LIFE.pdf"),
    ("APEX_EPEX_PERSONA_DAY_IN_LIFE.md", "APEX_EPEX_PERSONA_DAY_IN_LIFE.pdf"),
    ("APEX_ERCOT_PERSONA_DAY_IN_LIFE.md", "APEX_ERCOT_PERSONA_DAY_IN_LIFE.pdf"),
]


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TitleMain",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#1B365D"),
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading2Blue",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1B365D"),
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading3Dark",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=8,
            spaceAfter=2,
        )
    )
    return styles


def _clean_line(line: str) -> str:
    return line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def markdown_to_story(markdown_text: str, styles):
    story = []

    for raw in markdown_text.splitlines():
        line = raw.strip()
        if not line:
            story.append(Spacer(1, 0.08 * inch))
            continue

        if line == "---":
            hr = Table([[""]], colWidths=[7.1 * inch], rowHeights=[0.01 * inch])
            hr.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#CBD5E1")),
                        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ]
                )
            )
            story.append(hr)
            story.append(Spacer(1, 0.1 * inch))
            continue

        if line.startswith("# "):
            story.append(Paragraph(_clean_line(line[2:].strip()), styles["TitleMain"]))
            continue
        if line.startswith("## "):
            story.append(Paragraph(_clean_line(line[3:].strip()), styles["Heading2Blue"]))
            continue
        if line.startswith("### "):
            story.append(Paragraph(_clean_line(line[4:].strip()), styles["Heading3Dark"]))
            continue

        if line.startswith("- "):
            bullet = _clean_line(line[2:].strip())
            story.append(Paragraph(f"&bull; {bullet}", styles["BodySmall"]))
            continue

        story.append(Paragraph(_clean_line(line), styles["BodySmall"]))

    return story


def render_pdf(md_path: Path, pdf_path: Path):
    styles = build_styles()
    markdown_text = md_path.read_text(encoding="utf-8")
    story = markdown_to_story(markdown_text, styles)

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=LETTER,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title=md_path.stem.replace("_", " "),
        author="APEX Documentation",
    )
    doc.build(story)


def main():
    for md_name, pdf_name in MARKET_DOCS:
        md_path = DOCS / md_name
        pdf_path = DOCS / pdf_name
        if not md_path.exists():
            raise FileNotFoundError(f"Missing markdown source: {md_path}")
        render_pdf(md_path, pdf_path)
        print(f"Generated {pdf_path}")


if __name__ == "__main__":
    main()
