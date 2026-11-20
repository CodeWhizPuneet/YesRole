import re

from app.schemas import Evidence, Finding, ParsedResume, Requirement
from app.services.embedding_service import similarities
from app.services.job_parser import CERT, EDUCATION, SKILL_PATTERNS, year_count

NEGATED = re.compile(
    r"\b(?:no|not|without|lack(?:s|ing)?|never used|learning|planning to learn|want to learn)\s+(?:\w+\s+){0,4}$", re.I
)
NOT_YET = re.compile(r"^\s*(?:[:(\-–—]\s*)?(?:none\b|not (?:used|learned|yet)\b|in progress\b|beginner coursework\b)", re.I)
ACTION = re.compile(
    r"\b(built|developed|trained|created|implemented|wrote|evaluated|analy[sz]ed|designed|maintained|"
    r"deployed|automated|tested|managed|published|collaborated|produced|optimized|shipped|"
    r"delivered|led|performed|prepared|presented|monitored|generated|conducted|supported)\b", re.I
)
PROFESSIONAL = re.compile(r"\b(professional|work experience|commercial|industry|full.time|employment)\b", re.I)
NONPROFESSIONAL = re.compile(r"\b(?:personal projects?|hobby projects?|coursework|class projects?|"
                             r"(?:no|without|lack(?:s|ing)?)\s+(?:\w+\s+){0,3}(?:professional|industry|work) experience)\b", re.I)
CERT_IN_PROGRESS = re.compile(r"\b(preparing|studying|planning|candidate|in progress|coursework|"
                              r"training|aspiring|practice|expired|pending|expected|not (?:certified|earned|completed)|"
                              r"never (?:earned|completed))\b", re.I)
DATE_RANGE = re.compile(r"\b(20\d{2}|19\d{2})\s*[-–—]\s*(20\d{2}|19\d{2}|present|current)\b", re.I)
DEGREE_LEVELS = {
    "doctorate": r"\b(?:ph\.?d|doctorate|doctoral)\b",
    "master": r"\b(?:master|m\.?tech|m\.?sc?|m\.?a\.?)(?:'s)?\b",
    "bachelor": r"\b(?:bachelor|b\.?tech|b\.?sc?|b\.?a\.?)(?:'s)?\b",
    "diploma": r"\bdiploma\b",
}
FIELDS = {
    "computer science": r"\b(?:computer science|computing)\b",
    "statistics": r"\bstatistics\b",
    "mathematics": r"\b(?:mathematics|maths?)\b",
    "engineering": r"\bengineering\b",
    "data science": r"\bdata science\b",
    "information technology": r"\binformation technology\b",
    "business": r"\bbusiness\b",
}
RELATED = [{"PyTorch", "TensorFlow", "Keras"}, {"Tableau", "Power BI"}, {"PostgreSQL", "MySQL", "SQLite"},
           {"Azure", "AWS", "Google Cloud"}]


def positive_skills(text: str) -> set[str]:
    return {skill for skill, pattern in SKILL_PATTERNS.items() if any(
        not NEGATED.search(text[max(0, match.start() - 72):match.start()])
        and not NOT_YET.search(text[match.end():])
        for match in pattern.finditer(text)
    )}


def passages(resume: ParsedResume) -> list[tuple[str, str]]:
    result = []
    for section in resume.sections:
        for raw in section.text.splitlines():
            line = raw.lstrip("•–-* ").strip()
            if len(line) < 3:
                continue
            # Preserve exact source substrings while preventing very long inputs from being truncated.
            for clause in re.split(r"(?<=[.!?])\s+(?=[A-Z])", line):
                words = list(re.finditer(r"\S+", clause))
                for start in range(0, len(words), 70):
                    result.append((section.title, clause[words[start].start():words[min(start + 69, len(words) - 1)].end()]))
    return result[:450]


def required_skills_met(requirement: Requirement, skills: set[str]) -> bool:
    requested = set(requirement.skills)
    if not requested:
        return True
    if requested <= skills:
        return True
    if not re.search(r"\bor\b|/", requirement.text, re.I):
        return False
    for missing in requested - skills:
        left = SKILL_PATTERNS[missing].pattern
        if not any(
            re.search(rf"(?:{left}\s*(?:or|/)\s*{right}|{right}\s*(?:or|/)\s*{left})", requirement.text, re.I)
            for right in (SKILL_PATTERNS[skill].pattern for skill in requested & skills)
        ):
            return False
    return True


def certification_tokens(text: str) -> set[str]:
    words = set(re.findall(r"\b[a-z][a-z0-9-]+\b", text.lower()))
    stop = {"required", "must", "have", "a", "an", "the", "certification", "certifications",
            "certified", "certificate", "preferred", "hold", "valid", "current", "license",
            "licensed", "with", "or", "and", "is", "are", "completion", "completed", "active",
            "possess", "proof", "credential", "credentials", "in", "demonstrate", "evidence", "you"}
    return words - stop


def named_certification(requirement: Requirement, section: str, text: str) -> bool:
    identity = certification_tokens(requirement.text)
    qualified = section == "Certifications" or bool(CERT.search(text))
    codes = {token for token in identity if re.fullmatch(r"[a-z]{2}-\d{3}", token)}
    mentions = certification_tokens(text)
    return qualified and bool(identity) and (identity <= mentions or bool(codes & mentions)) and not CERT_IN_PROGRESS.search(text)


def degree_patterns(text: str, patterns: dict[str, str]) -> set[str]:
    return {name for name, pattern in patterns.items() if re.search(pattern, text, re.I)}


def classify(requirement: Requirement, rows, scores, extracted_skills=None) -> Finding:
    ranked = sorted(range(len(rows)), key=lambda index: float(scores[index]), reverse=True)
    evidence = None

    def choose(index):
        section, text = rows[index]
        return Evidence(section=section, text=text, similarity=round(float(scores[index]), 3))

    def result(status, explanation, index=None, additional=()):
        return Finding(requirement=requirement, status=status,
                       evidence=choose(index) if index is not None else evidence, explanation=explanation,
                       additional_evidence=[choose(i) for i in additional])

    skill_rows = extracted_skills if extracted_skills is not None else [positive_skills(text) for _, text in rows]
    if ranked and scores[ranked[0]] >= .28:
        evidence = choose(ranked[0])
    if requirement.category == "Certification":
        for i in ranked:
            if named_certification(requirement, *rows[i]):
                return result("Supported", "The resume explicitly lists the named credential.", i)
        return result("Not Evidenced", "No explicit evidence of the named credential was found.")
    if requirement.category == "Education":
        levels = degree_patterns(requirement.text, DEGREE_LEVELS)
        fields = degree_patterns(requirement.text, FIELDS)
        candidates = [i for i in ranked if rows[i][0] == "Education" and
                      (EDUCATION.search(rows[i][1]) or degree_patterns(rows[i][1], DEGREE_LEVELS))]
        for i in candidates:
            text = rows[i][1]
            level_matches = not levels or bool(levels & degree_patterns(text, DEGREE_LEVELS))
            field_matches = not fields or bool(fields & degree_patterns(text, FIELDS))
            ongoing = re.search(r"\b(expected|pursuing|in progress|candidate|enrolled)\b", text, re.I)
            allows_ongoing = re.search(r"\b(enrolled|pursuing|currently studying)\b", requirement.text, re.I)
            if level_matches and field_matches and bool(ongoing) == bool(allows_ongoing):
                return result("Supported", "The Education section explicitly lists the requested qualification.", i)
        if candidates:
            return result("Partially Supported", "Education is listed, but the degree, field or completion status is unclear.", candidates[0])
        return result("Not Evidenced", "No matching qualification was found in the Education section.")
    if requirement.category == "Experience":
        threshold = year_count(requirement.text)
        candidates = [i for i in ranked if not NONPROFESSIONAL.search(rows[i][1]) and (
            rows[i][0] == "Experience" or (rows[i][0] == "Summary" and PROFESSIONAL.search(rows[i][1]))
        )]
        relevant = [i for i in candidates if required_skills_met(requirement, skill_rows[i])]
        for i in relevant:
            text = rows[i][1]
            if threshold is None and (ACTION.search(text) or PROFESSIONAL.search(text)):
                return result("Supported", "The resume describes relevant work in an experience passage.", i)
            described = year_count(text)
            if threshold is not None and described is not None and described >= threshold:
                return result("Supported", "The resume explicitly states a sufficient duration with relevant work evidence.", i)
        if relevant:
            hint = " Relevant dates appear, but month-level duration was not inferred." if any(
                DATE_RANGE.search(rows[i][1]) for i in candidates) else ""
            return result("Partially Supported", "Relevant work appears, but the requested duration or scope is not explicit." + hint, relevant[0])
        return result("Not Evidenced", "No work passage demonstrates the requested professional experience and scope.")
    if requirement.skills:
        requested = set(requirement.skills)
        found = set().union(*skill_rows)
        strong = [i for i in ranked if skill_rows[i] & requested]
        if required_skills_met(requirement, found):
            if requirement.category == "Responsibility":
                task = [i for i in strong if required_skills_met(requirement, skill_rows[i])
                        and ACTION.search(rows[i][1]) and scores[i] >= .44]
                if not task:
                    return result("Partially Supported", "The named tools appear, but the resume does not clearly describe performing the task.", strong[0])
                return result("Supported", "A relevant action and the named skills appear together in the evidence.", task[0])
            index = next((i for i in strong if required_skills_met(requirement, skill_rows[i])), strong[0])
            covered = set(skill_rows[index])
            other = []
            for i in strong:
                if required_skills_met(requirement, covered):
                    break
                if (requested & skill_rows[i]) - covered:
                    other.append(i)
                    covered.update(skill_rows[i])
            return result("Supported", "The resume explicitly names the requested skills in the passages shown.", index, other)
        if strong:
            missing = ", ".join(sorted(requested - found))
            return result("Partially Supported", f"Some requested skills appear. Missing explicit evidence for {missing}.", strong[0])
        related = next((i for i in ranked if any(group & requested and group & skill_rows[i] for group in RELATED)), None)
        if related is not None:
            return result("Partially Supported", "Related tooling appears, but the requested skill is not named.", related)
        return result("Not Evidenced", "None of the requested skills appear explicitly. Semantic resemblance alone is insufficient.")
    for i in ranked:
        # Unknown technologies and domain qualifications receive a conservative label.
        if scores[i] >= .66 and ACTION.search(rows[i][1]) and requirement.category == "Responsibility":
            return result("Supported", "A concrete resume action closely matches the responsibility in meaning.", i)
    if evidence and evidence.similarity >= .46:
        return result("Partially Supported", "A related passage was retrieved, but it does not establish the full qualification.")
    return result("Not Evidenced", "No strong supporting passage was found.")


def match(resume: ParsedResume, requirements: list[Requirement]) -> list[Finding]:
    rows = passages(resume)
    skills = [positive_skills(text) for _, text in rows]
    scores = similarities([requirement.text for requirement in requirements], [row[1] for row in rows])
    return [classify(requirement, rows, scores[index], skills) for index, requirement in enumerate(requirements)]

