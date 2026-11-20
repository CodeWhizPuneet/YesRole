import re

from app.schemas import Finding, ParsedResume, Suggestion
from app.services.job_parser import SKILL_PATTERNS

PREFIXES = {
    "I was responsible for ": "Responsible for ",
    "I worked on ": "Worked on ",
    "I helped to ": "Helped ",
    "I helped ": "Helped ",
    "I developed ": "Developed ",
    "I created ": "Created ",
    "I built ": "Built ",
    "I analyzed ": "Analyzed ",
    "I analysed ": "Analysed ",
    "I implemented ": "Implemented ",
    "I collaborated ": "Collaborated ",
    "I tested ": "Tested ",
    "I maintained ": "Maintained ",
    "In order to ": "To ",
}


def prioritize_skills(line: str, relevant: set[str]) -> str:
    if "," not in line:
        return line
    values = [part.strip() for part in line.split(",")]
    identified = [next((skill for skill, pattern in SKILL_PATTERNS.items() if pattern.fullmatch(value)), "")
                  for value in values]
    if not all(identified):
        return line
    ordered = sorted(range(len(values)), key=lambda index: identified[index] not in relevant)
    if ordered == list(range(len(values))):
        return line
    return ", ".join(values[index] for index in ordered)


def recommend(resume: ParsedResume, findings: list[Finding]) -> list[Suggestion]:
    suggestions = []
    gaps = sorted(findings, key=lambda item: (item.requirement.priority != "Required", item.status != "Not Evidenced"))
    for finding in gaps:
        if finding.status == "Supported":
            continue
        requirement = finding.requirement
        suggestions.append(Suggestion(
            id=requirement.id, kind="Needs User Confirmation", title=requirement.text,
            detail=f"{requirement.priority}. {finding.explanation} Add specific evidence only if you can verify it from your own experience.",
        ))
    seen = set()
    requested_skills = {skill for finding in findings for skill in finding.requirement.skills}
    for section in resume.sections:
        if section.title == "Skills":
            for line in section.text.splitlines():
                reordered = prioritize_skills(line, requested_skills)
                if reordered != line and line not in seen:
                    seen.add(line)
                    suggestions.append(Suggestion(
                        id=f"rewrite-{len(seen)}", kind="Safe Rephrasing", title="Move target skills to the front",
                        detail="Reorders existing skills to make the role-relevant ones easier to find.",
                        original=line, replacement=reordered,
                    ))
                if len(seen) >= 10:
                    return suggestions
        if section.title not in {"Summary", "Projects", "Experience"}:
            continue
        for line in section.text.splitlines():
            for prefix, replacement in PREFIXES.items():
                pattern = re.compile(r"^([•–*-]?\s*)" + re.escape(prefix), re.I)
                rewritten = pattern.sub(lambda match: match[1] + replacement, line, count=1)
                if rewritten == line or line in seen:
                    continue
                seen.add(line)
                suggestions.append(Suggestion(
                    id=f"rewrite-{len(seen)}", kind="Safe Rephrasing",
                    title=f"Clarify a line in {section.title}",
                    detail="Tightens phrasing while preserving the original action and claims.",
                    original=line, replacement=rewritten,
                ))
                break
            if len(seen) == 10:
                return suggestions
    return suggestions

