from __future__ import annotations

import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer


def register_fonts() -> tuple[str, str, str]:
    regular = Path(r"C:\Windows\Fonts\times.ttf")
    bold = Path(r"C:\Windows\Fonts\timesbd.ttf")
    italic = Path(r"C:\Windows\Fonts\timesi.ttf")
    pdfmetrics.registerFont(TTFont("TimesNewRoman", str(regular)))
    pdfmetrics.registerFont(TTFont("TimesNewRoman-Bold", str(bold)))
    pdfmetrics.registerFont(TTFont("TimesNewRoman-Italic", str(italic)))
    return "TimesNewRoman", "TimesNewRoman-Bold", "TimesNewRoman-Italic"


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def inline_md(text: str) -> str:
    text = xml_escape(text)
    text = re.sub(r"`([^`]+)`", r"<font name='TimesNewRoman-Italic'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    return text


def page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("TimesNewRoman", 12)
    canvas.drawCentredString(A4[0] / 2, 1.25 * cm, str(doc.page))
    canvas.restoreState()


def build_pdf(md_path: Path, pdf_path: Path) -> None:
    font, bold, italic = register_fonts()

    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "DisserBody",
        parent=styles["Normal"],
        fontName=font,
        fontSize=14,
        leading=21,
        firstLineIndent=1.25 * cm,
        alignment=TA_JUSTIFY,
        spaceBefore=0,
        spaceAfter=0,
    )
    item = ParagraphStyle(
        "DisserItem",
        parent=body,
        firstLineIndent=0,
        leftIndent=1.25 * cm,
    )
    h1 = ParagraphStyle(
        "DisserH1",
        parent=body,
        fontName=bold,
        firstLineIndent=0,
        alignment=TA_CENTER,
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True,
    )
    h2 = ParagraphStyle(
        "DisserH2",
        parent=body,
        fontName=bold,
        firstLineIndent=1.25 * cm,
        alignment=TA_LEFT,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=3 * cm,
        rightMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=md_path.stem,
        author="Тинишов Вадим Сергеевич",
    )

    flow = []
    previous_was_title_block = False
    for raw in md_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            title = line[2:].strip()
            if title in {"Реферат", "Общая характеристика диссертационной работы"}:
                flow.append(PageBreak())
            flow.append(Paragraph(inline_md(title), h1))
            previous_was_title_block = True
        elif line.startswith("## "):
            flow.append(Paragraph(inline_md(line[3:].strip()), h2))
            previous_was_title_block = False
        elif re.match(r"^(\d+\.|[-*])\s+", line):
            flow.append(Paragraph(inline_md(line), item))
            previous_was_title_block = False
        else:
            # Keep title page lines centered until the generated "Оглавление" heading begins.
            if previous_was_title_block and line.isupper():
                centered = ParagraphStyle("CenteredTitle", parent=body, firstLineIndent=0, alignment=TA_CENTER, fontName=bold)
                flow.append(Paragraph(inline_md(line), centered))
            else:
                flow.append(Paragraph(inline_md(line), body))
            previous_was_title_block = False

    doc.build(flow, onFirstPage=page_number, onLaterPages=page_number)


if __name__ == "__main__":
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    build_pdf(src, dst)
    print(dst)
