import re

from app.schemas import InputError, Requirement

TAXONOMY = {
    "Python": ["python"], "Java": ["java"], "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript"], "C++": ["c++"], "C#": ["c#"], "Go": ["golang", "go programming", "go language"],
    "SQL": ["sql", "structured query language"], "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"], "MongoDB": ["mongodb"], "Redis": ["redis"], "SQLite": ["sqlite"],
    "Docker": ["docker"], "Kubernetes": ["kubernetes", "k8s"], "Terraform": ["terraform"],
    "PyTorch": ["pytorch"], "TensorFlow": ["tensorflow"], "Keras": ["keras"],
    "scikit-learn": ["scikit-learn", "scikit learn", "sklearn"],
    "pandas": ["pandas"], "NumPy": ["numpy"], "SciPy": ["scipy"], "Matplotlib": ["matplotlib"],
    "FastAPI": ["fastapi"], "Django": ["django"], "Flask": ["flask"], "React": ["react", "react.js", "reactjs"],
    "Node.js": ["node.js", "nodejs"], "Vue": ["vue.js", "vuejs"], "Git": ["git"],
    "GitHub Actions": ["github actions"], "CI/CD": ["ci/cd", "continuous integration", "continuous delivery"],
    "Azure": ["azure"], "AWS": ["aws", "amazon web services"], "Google Cloud": ["gcp", "google cloud"],
    "Linux": ["linux"], "REST": ["rest", "restful"], "GraphQL": ["graphql"],
    "Spark": ["apache spark", "pyspark"], "Airflow": ["airflow"], "Hadoop": ["hadoop"],
    "Tableau": ["tableau"], "Power BI": ["power bi"], "Excel": ["excel"], "Google Sheets": ["google sheets"],
    "ETL": ["etl", "extract transform load", "extract, transform, load"],
    "NLP": ["nlp", "natural language processing"], "Computer Vision": ["computer vision"],
    "Machine Learning": ["machine learning", "ml models"], "Deep Learning": ["deep learning"],
    "A/B Testing": ["a/b testing", "split testing"], "Unit Testing": ["unit testing", "unit tests"],
    "Statistics": ["statistics", "statistical analysis"], "R": ["r programming", "r language", "rstudio"],
    "Model Evaluation": ["model evaluation", "evaluate models", "evaluated models"],
    "Data Visualization": ["data visualization", "data visualisation"], "Data Analysis": ["data analysis", "data analytics"],
    "LLMs": ["llm", "llms", "large language models"], "RAG": ["rag", "retrieval-augmented generation"],
    "MLflow": ["mlflow"], "Java Spring": ["spring boot"], "Bash": ["bash"], "SAS": ["sas"],
}
SKILL_PATTERNS = {
    skill: re.compile(r"(?<![\w+#])(?:" + "|".join(map(re.escape, aliases)) + r")(?![\w+#])", re.I)
    for skill, aliases in TAXONOMY.items()
}
YEARS = re.compile(r"(\d+(?:\.\d+)?)\s*(?:\+|[-–]\s*\d+)?\s*(?:years?|yrs?)\b", re.I)
MINIMUM_YEARS = re.compile(r"\b(?:at least|minimum(?: of)?)\s*(\d+(?:\.\d+)?)\b", re.I)
PREFERRED = re.compile(r"\b(preferred|nice to have|bonus|desirable|a plus|optional|advantage)\b", re.I)
MANDATORY = re.compile(r"\b(must|required|essential|mandatory|minimum|at least)\b", re.I)
CERT = re.compile(r"\b(certifications?|certified|licenses?|licensed|az-900|ai-900|dp-900)\b", re.I)
EDUCATION = re.compile(r"\b(degree|bachelor'?s?|master'?s?|ph\.?d|diploma|b\.?s\.?(?=\s+in\b)|m\.?s\.?(?=\s+in\b)|b\.?tech|m\.?tech|currently (?:enrolled|pursuing))\b", re.I)
SIGNAL = re.compile(r"\b(experience|proficiency|familiarity|knowledge|ability|skills?|expertise|understanding|"
                    r"build|develop|design|implement|collaborate|analy[sz]e|deploy|maintain|write|train|evaluate|"
                    r"create|communicate|support|work with|assist|deliver|prepare|monitor|enrolled|pursuing)\b", re.I)
TASK = re.compile(r"^(?:you (?:will|would)\s+)?(?:build|design|develop|implement|collaborate|analy[sz]e|"
                  r"deploy|maintain|write|train|evaluate|create|prepare|deliver|monitor|communicate|"
                  r"support|assist|work with)\b", re.I)
ROLE_TITLE = re.compile(r"\b(?:intern(?:ship)?|engineer|analyst|developer|scientist|specialist|manager|designer|"
                        r"architect|associate|consultant|administrator)\s*(?:\([^)]*\))?$", re.I)
SKIP_HEADINGS = {"about us", "about the company", "who we are", "benefits", "what we offer",
                 "compensation", "how to apply", "equal opportunity", "perks",
                 "company overview", "about the team", "perks and benefits"}
REQUIRED_HEADINGS = {"requirements", "job requirements", "qualifications", "required", "required skills",
                     "required qualifications", "minimum qualifications", "minimum requirements",
                     "must have", "must-have skills", "essential skills", "what you bring",
                     "what you'll need", "technical skills", "what we are looking for", "about you"}
PREFERRED_HEADINGS = {"preferred", "preferred skills", "preferred qualifications", "desired qualifications",
                      "desirable", "nice to have", "nice-to-have", "bonus", "bonus skills"}
RESPONSIBILITY_HEADINGS = {"responsibilities", "key responsibilities", "what you'll do", "what you will do", "duties"}
SKIP_LINE = re.compile(r"^(?:we (?:are|offer|provide|believe|value)|our (?:team|company|mission|culture)|"
                       r"the company|about us|salary|compensation|equal opportunity|apply now|location:|"
                       r"employment type:|job title:|join us|you will (?:receive|enjoy))\b", re.I)
MAX_REQUIREMENTS = 45

def detect_skills(text: str) -> list[str]:
    return [skill for skill, pattern in SKILL_PATTERNS.items() if pattern.search(text)]


def year_count(text: str) -> float | None:
    match = YEARS.search(text) or MINIMUM_YEARS.search(text)
    return float(match[1]) if match else None


def category(text: str, skills: list[str], block: str) -> str:
    if CERT.search(text):
        return "Certification"
    if EDUCATION.search(text):
        return "Education"
    if year_count(text) is not None or re.search(r"\bprofessional experience\b", text, re.I):
        return "Experience"
    if block == "responsibility" or TASK.match(text):
        return "Responsibility"
    if skills:
        return "Technical skills"
    if re.search(r"\bknowledge|domain\b", text, re.I):
        return "Domain knowledge"
    return "Qualification"


def parse_job(description: str) -> list[Requirement]:
    priority, block = "Required", ""
    seen, requirements = set(), []
    lines = [line.strip() for line in description.splitlines() if line.strip()]
    for index, raw in enumerate(lines):
        line = re.sub(r"^(?:[•●▪*–-]|\d+[.)])\s*", "", raw)
        if index == 0 and len(line.split()) <= 8 and ROLE_TITLE.search(line) and not (
            SIGNAL.search(line) or EDUCATION.search(line) or year_count(line) is not None
        ):
            continue
        label, separator, tail = line.partition(":")
        key = label.strip().casefold().rstrip(".")
        is_heading = len(label.split()) <= 6 and (bool(separator) or len(line.split()) <= 6)
        if is_heading:
            if key in SKIP_HEADINGS:
                block = "skip"
                priority = "Required"
                continue
            if key in {"about the role", "job overview"}:
                block, priority = "responsibility", "Required"
                line = tail.strip()
            if key in REQUIRED_HEADINGS:
                block, priority = "requirements", "Required"
                line = tail.strip()
            elif key in PREFERRED_HEADINGS:
                block, priority = "requirements", "Preferred"
                line = tail.strip()
            elif key in RESPONSIBILITY_HEADINGS:
                block, priority = "responsibility", "Required"
                line = tail.strip()
        if not line or block == "skip" or SKIP_LINE.match(line):
            continue
        for clause in re.split(r";\s+|(?<=[.!?])\s+(?=[A-Z])", line):
            clause = clause.strip()
            skills = detect_skills(clause)
            signal = skills or CERT.search(clause) or EDUCATION.search(clause) or year_count(clause) is not None
            if not (signal or SIGNAL.search(clause) or MANDATORY.search(clause)):
                continue
            if len(clause) > 1200:
                raise InputError("Split long job description paragraphs into individual requirements of up to 1,200 characters.")
            unique = re.sub(r"[\W_]+", " ", clause.casefold()).strip()
            if unique in seen:
                continue
            if len(requirements) == MAX_REQUIREMENTS:
                raise InputError(f"Include up to {MAX_REQUIREMENTS} distinct job requirements per analysis.")
            seen.add(unique)
            rank = "Preferred" if PREFERRED.search(clause) else "Required" if MANDATORY.search(clause) else priority
            requirements.append(Requirement(id=f"R{len(requirements) + 1:02}", text=clause,
                                            category=category(clause, skills, block), priority=rank, skills=skills))
    if not requirements:
        raise InputError("No job requirements were found. Include skills, qualifications, or responsibilities on separate lines.")
    return requirements

