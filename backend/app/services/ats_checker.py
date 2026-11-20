import re

from app.schemas import Check, ParsedResume

EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", re.I)
PHONE = re.compile(r"(?<![\w.])\+?\d[\d .()-]{7,17}\d(?![\w.])")
DATES = {
    "numeric": re.compile(r"\b(?:0?[1-9]|1[0-2])[/.-](?:19|20)\d{2}\b"),
    "named": re.compile(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
                        r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?\s+(?:19|20)\d{2}\b", re.I),
}


def check(resume: ParsedResume) -> list[Check]:
    headings = {section.title for section in resume.sections if section.title != "Contact"}
    empty = [section.title for section in resume.sections if section.title != "Contact" and not section.text]
    phone = any(len(re.sub(r"\D", "", match[0])) >= 9 for match in PHONE.finditer(resume.text))
    email_found = bool(EMAIL.search(resume.text))
    missing = [label for label, found in [("email", email_found), ("phone", phone)] if not found]
    date_types = [name for name, pattern in DATES.items() if pattern.search(resume.text)]
    result = [
        Check(name="Selectable text" if resume.source != "Text" else "Text input", status="Pass",
              detail=f"{len(resume.text):,} readable characters are available for analysis."),
        Check(name="Recognizable headings", status="Pass" if len(headings) >= 2 else "Warning",
              detail=f"Recognized {len(headings)} resume headings. Use standard headings such as Skills and Experience."),
        Check(name="Contact information", status="Warning" if missing else "Pass",
              detail="Could not identify a readable " + " or ".join(missing) + "." if missing else
              "An email address and phone-like number were detected."),
        Check(name="Section content", status="Issue" if empty else "Pass" if headings else "Warning",
              detail=f"Empty heading(s): {', '.join(empty)}." if empty else
              "Recognized sections contain text." if headings else "No standard section headings were recognized."),
        Check(name="Date consistency", status="Warning" if len(date_types) != 1 else "Pass",
              detail="Use a consistent month and year format." if date_types else
              "No month-and-year dates were recognized. Check dates if they are relevant to your experience."),
    ]
    if not {"Experience", "Projects"} & headings:
        result.append(Check(name="Experience sections", status="Warning",
                            detail="No Experience or Projects heading was found. Use an appropriate heading to make evidence easier to find."))
    for warning in resume.warnings:
        result.append(Check(name="Document formatting", status="Warning", detail=warning))
    return result

