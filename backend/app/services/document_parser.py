import io
import re
import unicodedata
import zipfile

import pymupdf
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.schemas import InputError, ParsedResume, Section

MAX_FILE = 5 * 1024 * 1024
MAX_PAGES = 30
HEADINGS = {
    "summary": "Summary", "professional summary": "Summary", "profile": "Summary",
    "objective": "Summary", "about me": "Summary", "career objective": "Summary",
    "skills": "Skills", "technical skills": "Skills", "tools": "Skills",
    "technologies": "Skills", "core competencies": "Skills",
    "experience": "Experience", "work experience": "Experience", "employment": "Experience",
    "professional experience": "Experience", "internships": "Experience", "work history": "Experience",
    "projects": "Projects", "selected projects": "Projects", "personal projects": "Projects",
    "education": "Education", "academic background": "Education",
    "certifications": "Certifications", "licenses and certifications": "Certifications",
    "courses and certifications": "Certifications", "awards": "Awards",
    "publications": "Publications", "volunteering": "Volunteering",
    "contact": "Contact", "contact information": "Contact",
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", text)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(
        re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")
    )).strip()


def heading(line: str) -> str | None:
    return HEADINGS.get(line.strip().rstrip(":").strip().casefold())


def sections(text: str) -> list[Section]:
    result = []
    title, lines = "Contact", []
    for line in text.splitlines():
        name = heading(line)
        if name:
            if lines or title != "Contact":
                result.append(Section(title=title, text="\n".join(lines).strip()))
            title, lines = name, []
        else:
            lines.append(line)
    result.append(Section(title=title, text="\n".join(lines).strip()))
    return result


def parse_text(text: str, source="Text", warnings=None) -> ParsedResume:
    cleaned = normalize(text)
    if len(cleaned) < 30:
        message = "The resume needs at least 30 characters of readable text."
        if source == "PDF":
            message = "This PDF has too little selectable text. It may be image-only. Upload a text-based PDF or DOCX, or paste the resume text."
        raise InputError(message)
    if len(cleaned) > 60_000:
        raise InputError("The extracted resume exceeds 60,000 characters.")
    return ParsedResume(text=cleaned, sections=sections(cleaned), source=source, warnings=warnings or [])


def parse_file(filename: str, data: bytes) -> ParsedResume:
    if not data or len(data) > MAX_FILE:
        raise InputError("Upload a non-empty file of 5 MB or less.")
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in {"pdf", "docx"}:
        raise InputError("Upload a PDF or DOCX resume.")
    warnings: list[str] = []
    try:
        if ext == "pdf":
            if not data.startswith(b"%PDF-"):
                raise InputError("The upload is not a valid PDF.")
            with pymupdf.open(stream=data, filetype="pdf") as document:
                if document.needs_pass:
                    raise InputError("Remove the PDF password before uploading.")
                if len(document) > MAX_PAGES:
                    raise InputError("Upload a PDF with 30 pages or fewer.")
                pages = [page.get_text(sort=True) for page in document]
                if any(not page.strip() for page in pages):
                    warnings.append("A PDF page has no selectable text. Check for scanned or blank pages.")
                if any(page.get_images() for page in document):
                    warnings.append("The PDF contains images. Check whether important information is present as selectable text.")
                return parse_text("\n\n".join(pages), "PDF", warnings)

        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > 1000 or sum(entry.file_size for entry in entries) > 25 * 1024 * 1024:
                raise InputError("The expanded DOCX exceeds document limits.")
            names = set(archive.namelist())
            if not {"word/document.xml", "[Content_Types].xml"} <= names:
                raise InputError("The upload is not a valid DOCX.")
        document = Document(io.BytesIO(data))
        lines = []
        for item in document.iter_inner_content():
            if isinstance(item, Paragraph):
                lines.append(item.text)
            elif isinstance(item, Table):
                warning = "The DOCX uses tables. Check the reading order before submitting."
                if warning not in warnings:
                    warnings.append(warning)
                for row in item.rows:
                    cells = list(dict.fromkeys(cell.text for cell in row.cells))
                    lines.append(" | ".join(cells))
        return parse_text("\n".join(lines), "DOCX", warnings)
    except InputError:
        raise
    except Exception:
        raise InputError(f"The {ext.upper()} could not be opened. Try another file or paste the resume text.") from None

