import numpy as np
import pytest

from app.services.document_parser import parse_text
from app.services.job_parser import parse_job
from app.services.matching_engine import classify, passages
from app.services.optimization_engine import recommend
from app.services.scoring_engine import score


def finding(description, text, similarity=.89):
    requirement = parse_job(description)[0]
    rows = passages(parse_text(text))
    return classify(requirement, rows, np.full(len(rows), similarity))


def test_parser_skips_title_and_marketing_and_captures_preferred():
    requirements = parse_job("Machine Learning Engineer Intern\nAbout us\nWe are a fast-growing Python company.\nMinimum Qualifications:\n"
                             "- At least 3 years of professional experience with Django.\n"
                             "Required Skills: Python and Docker\nPreferred qualifications:\n"
                             "GitHub Actions is a plus.\nBenefits:\nFree Java classes.")
    assert [item.id for item in requirements] == ["R01", "R02", "R03"]
    assert [item.priority for item in requirements] == ["Required", "Required", "Preferred"]
    assert requirements[0].category == "Experience"
    assert requirements[1].text == "Python and Docker"
    assert requirements[2].skills == ["GitHub Actions"]


def test_short_skill_and_split_passage_evidence():
    assert parse_job("Required qualifications:\nC++\nSQL")[0].skills == ["C++"]
    report = finding("Experience using Python and Docker.", "Experience\nDeveloped test tools using Python.\nPackaged services with Docker.")
    assert report.status == "Supported"
    assert "Docker" in report.additional_evidence[0].text


@pytest.mark.parametrize("job,resume,expected", [
    ("Experience with Docker is required.", "Skills\nPython\nProjects\nBuilt a Python pipeline to test models.", "Not Evidenced"),
    ("Experience with PyTorch is required.", "Skills\nTensorFlow\nProjects\nTrained an image model in TensorFlow.", "Partially Supported"),
    ("Knowledge of structured query language.", "Projects\nDesigned schemas and used SQL for querying logs.", "Supported"),
    ("Experience with Django or FastAPI.", "Projects\nDeveloped a service in Django for a club.", "Supported"),
    ("Experience with Django or FastAPI and Docker.", "Projects\nDeveloped a service in Django for a club.", "Partially Supported"),
    ("Docker is required.", "Summary\nI have no experience with Docker or containers.", "Not Evidenced"),
    ("Docker is required.", "Skills\nDocker: not used. Built a Python application.", "Not Evidenced"),
    ("3 years of professional Python experience.", "Projects\nBuilt Python websites for 4 years as personal projects.", "Not Evidenced"),
    ("3 years of professional experience with Python.", "Experience\n2 years of professional experience with Python.", "Partially Supported"),
    ("3 years of professional experience with Python.", "Summary\n4 years of professional experience with Python.", "Supported"),
    ("3 years of professional experience with Python.", "Summary\nNo professional experience, only 4 years of Python projects.", "Not Evidenced"),
    ("Microsoft Azure Fundamentals (AZ-900) certification.", "Certifications\nAZ-900, Microsoft Certified. Awarded in 2024.", "Supported"),
    ("Microsoft Azure Fundamentals (AZ-900) certification.", "Certifications\nPreparing for AZ-900. Practice assessment.", "Not Evidenced"),
    ("Microsoft Azure Fundamentals (AZ-900) certification.", "Certifications\nNot certified for AZ-900. Read the study syllabus.", "Not Evidenced"),
    ("Bachelor's degree in Computer Science required.", "Education\nBachelor's in Computer Science, expected May 2027.", "Partially Supported"),
])
def test_verification_rules(job, resume, expected):
    assert finding(job, resume).status == expected


def test_score_renormalizes_and_ignores_unproven_similarity():
    gap = finding("Experience with Docker is required.", "Skills\nPython\nProjects\nBuilt a Python pipeline to test models.")
    value, dimensions = score([gap])
    assert value == 0
    assert sum(item.weight for item in dimensions) == pytest.approx(100)
    assert "Preferred qualification coverage" not in {item.name for item in dimensions}


def test_safe_rewrites_preserve_claims_and_never_apply_gaps():
    parsed = parse_text("Projects\nI helped to develop a Python pipeline for a library.")
    gap = finding("Experience with Docker is required.", parsed.text)
    missing, rewrite = recommend(parsed, [gap])
    assert missing.kind == "Needs User Confirmation" and missing.replacement is None
    assert rewrite.kind == "Safe Rephrasing"
    assert rewrite.replacement == "Helped develop a Python pipeline for a library."

