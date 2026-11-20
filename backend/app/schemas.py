from typing import Literal

from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated

ResumeText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=30, max_length=60_000)]
JobText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=25, max_length=24_000)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
Status = Literal["Supported", "Partially Supported", "Not Evidenced"]


class InputError(ValueError):
    pass


class Section(BaseModel):
    title: str
    text: str


class ResumeInput(BaseModel):
    resume: ResumeText


class ParsedResume(BaseModel):
    text: str
    sections: list[Section]
    source: Literal["PDF", "DOCX", "Text"]
    warnings: list[str] = Field(default_factory=list)


class JobInput(BaseModel):
    description: JobText


class MatchInput(JobInput, ResumeInput):
    title: Title
    company: str = Field(default="", max_length=120)
    version: str = Field(default="Original resume", max_length=120)
    source: Literal["PDF", "DOCX", "Text"] = "Text"
    warnings: list[str] = Field(default_factory=list, max_length=10)


class Requirement(BaseModel):
    id: str
    text: str
    category: str
    priority: Literal["Required", "Preferred"]
    skills: list[str]
    weight: float = 1


class Evidence(BaseModel):
    section: str
    text: str
    similarity: float


class Finding(BaseModel):
    requirement: Requirement
    status: Status
    evidence: Evidence | None
    explanation: str
    additional_evidence: list[Evidence] = Field(default_factory=list)


class Dimension(BaseModel):
    name: str
    value: float
    weight: float


class Check(BaseModel):
    name: str
    status: Literal["Pass", "Issue", "Warning"]
    detail: str


class Suggestion(BaseModel):
    id: str
    kind: Literal["Safe Rephrasing", "Needs User Confirmation"]
    title: str
    detail: str
    original: str | None = None
    replacement: str | None = None


class Analysis(BaseModel):
    id: str
    created_at: str
    title: str
    company: str
    version: str
    score: int
    dimensions: list[Dimension]
    findings: list[Finding]
    ats: list[Check]
    suggestions: list[Suggestion]
    model: str
    parent_id: str | None = None


class AnalysisSummary(BaseModel):
    id: str
    created_at: str
    title: str
    company: str
    version: str
    score: int
    supported: int
    total: int
    parent_id: str | None = None
    change: int | None = None


class ExportInput(ResumeInput):
    format: Literal["pdf", "docx"]


class RevisionInput(ResumeInput):
    original_id: str
    description: JobText
    version: Title = "Revised resume"

