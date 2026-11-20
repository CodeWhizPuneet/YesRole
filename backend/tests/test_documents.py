import io

import pymupdf
import pytest
from docx import Document

from app.schemas import InputError
from app.services import ats_checker, document_parser, export_service

TEXT = """Alex Morgán
alex.morgan@example.com | +1 202 555 0142
Skills
Python, SQL
Projects
Built a searchable library index in Python.
Education
Bachelor's degree, expected May 2027"""


@pytest.mark.parametrize("file,exporter", [("resume.pdf", export_service.export_pdf), ("resume.docx", export_service.export_docx)])
def test_export_round_trips(file, exporter):
    result = document_parser.parse_file(file, exporter(TEXT))
    assert "alex.morgan@example.com" in result.text
    assert "Alex Morgán" in result.text
    assert "Built a searchable library index in Python." in result.text
    assert [section.title for section in result.sections] == ["Contact", "Skills", "Projects", "Education"]


def test_docx_tables_preserve_order_and_warn():
    doc = Document()
    doc.add_heading("Experience", level=1)
    doc.add_table(rows=1, cols=2).rows[0].cells[0].text = "Developed a portfolio tracker using Python."
    doc.add_paragraph("Published documentation for the project.")
    buffer = io.BytesIO()
    doc.save(buffer)
    parsed = document_parser.parse_file("resume.docx", buffer.getvalue())
    assert parsed.text.index("Developed") < parsed.text.index("Published")
    assert "tables" in parsed.warnings[0]


def test_image_only_pdf_message():
    with pymupdf.open() as document:
        document.new_page()
        with pytest.raises(InputError, match="image-only"):
            document_parser.parse_file("empty.pdf", document.tobytes())


@pytest.mark.parametrize("name,data", [
    ("empty.pdf", b""), ("invalid.pdf", b"invalid"), ("bad.docx", b"not a zip"),
    ("bad.txt", b"readable"), ("oversized.docx", b"x" * (document_parser.MAX_FILE + 1)),
], ids=["empty", "invalid-pdf", "invalid-docx", "unsupported-extension", "oversized"])
def test_invalid_document(name, data):
    with pytest.raises(InputError):
        document_parser.parse_file(name, data)


def test_empty_text_and_readability_warnings():
    with pytest.raises(InputError):
        document_parser.parse_text(" \n ")
    checks = {item.name: item.status for item in ats_checker.check(document_parser.parse_text(
        "Alex Morgan\nSkills\nEducation\nCoursework from Jan 2024 to 03/2025"
    ))}
    assert checks["Contact information"] == "Warning"
    assert checks["Section content"] == "Issue"
    assert checks["Date consistency"] == "Warning"

