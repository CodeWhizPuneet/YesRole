from statistics import mean

from app.schemas import Dimension, Finding
from app.services.matching_engine import ACTION

CREDIT = {"Supported": 1, "Partially Supported": .5, "Not Evidenced": 0}


def coverage(findings: list[Finding]) -> float | None:
    if not findings:
        return None
    return sum(CREDIT[item.status] * item.requirement.weight for item in findings) / sum(
        item.requirement.weight for item in findings
    )


def score(findings: list[Finding]) -> tuple[int, list[Dimension]]:
    required = [item for item in findings if item.requirement.priority == "Required" and
                item.requirement.category != "Experience"]
    preferred = [item for item in findings if item.requirement.priority == "Preferred"]
    experience = [item for item in findings if item.requirement.priority == "Required" and
                  item.requirement.category == "Experience"]
    evidenced = [item.evidence for item in findings if item.evidence and CREDIT[item.status]]
    dimensions = [
        ("Required qualification coverage", 45, coverage(required)),
        ("Preferred qualification coverage", 15, coverage(preferred)),
        ("Semantic relevance", 20, mean(
            max(0, item.evidence.similarity) * CREDIT[item.status] if item.evidence else 0 for item in findings
        )),
        ("Experience alignment", 15, coverage(experience)),
        ("Evidence quality", 5, sum(
            evidence.section in {"Experience", "Projects"} and bool(ACTION.search(evidence.text))
            for evidence in evidenced
        ) / len(findings)),
    ]
    weight_total = sum(weight for _, weight, value in dimensions if value is not None)
    breakdown = [
        Dimension(name=name, value=round(value * 100, 1), weight=round(weight * 100 / weight_total, 1))
        for name, weight, value in dimensions if value is not None
    ]
    overall = sum(weight * value for _, weight, value in dimensions if value is not None) / weight_total
    return round(100 * overall), breakdown

