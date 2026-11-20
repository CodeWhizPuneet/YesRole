from io import BytesIO

import pymupdf
from docx import Document
from docx.shared import Inches, Pt

from app.services.document_parser import heading


def export_docx(text: str) -> bytes:
    document = Document()
    section = document.sections[0]
    section.left_margin = section.right_margin = Inches(.75)
    normal = document.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(5)
    for index, line in enumerate(text.splitlines()):
        if not line:
            continue
        if heading(line):
            document.add_heading(line.rstrip(":"), level=1)
        elif index == 0 and len(line) < 70:
            document.add_heading(line, level=0)
        else:
            document.add_paragraph(line)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def wrap(line: str, font, size: int, max_width: int):
    current = ""
    for word in line.split():
        candidate = f"{current} {word}".strip()
        if current and font.text_length(candidate, fontsize=size) > max_width:
            yield current
            current = ""
        while font.text_length(word, fontsize=size) > max_width:
            end = 1
            while font.text_length(word[:end + 1], fontsize=size) <= max_width:
                end += 1
            yield word[:end]
            word = word[end:]
        current = f"{current} {word}".strip()
    if current:
        yield current


def export_pdf(text: str) -> bytes:
    with pymupdf.open() as document:
        page = document.new_page(width=612, height=792)
        writer = pymupdf.TextWriter(page.rect)
        normal, bold = pymupdf.Font("helv"), pymupdf.Font("hebo")
        y = 55
        for index, line in enumerate(text.splitlines()):
            if not line:
                y += 5
                continue
            is_heading = heading(line)
            size = 18 if index == 0 and len(line) < 70 else 13 if is_heading else 10
            font = bold if (is_heading or size == 18) and line.isascii() else normal
            if is_heading:
                y += 7
            for part in wrap(line, font, size, 508):
                if y > 735:
                    writer.write_text(page)
                    page = document.new_page(width=612, height=792)
                    writer = pymupdf.TextWriter(page.rect)
                    y = 55
                writer.append((52, y), part, font=font, fontsize=size)
                y += size + 5
        writer.write_text(page)
        document.subset_fonts()
        return document.tobytes(garbage=4, deflate=True)

