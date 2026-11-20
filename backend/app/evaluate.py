import json
from pathlib import Path

from sklearn.metrics import classification_report, confusion_matrix

from app.services.document_parser import parse_text
from app.services.job_parser import parse_job
from app.services.matching_engine import match

LABELS = ["Supported", "Partially Supported", "Not Evidenced"]


def main():
    cases = json.loads((Path(__file__).resolve().parents[1] / "evaluation" / "cases.json").read_text(encoding="utf-8"))
    actual, predicted = [], []
    for case in cases:
        result, = match(parse_text(case["resume"]), parse_job(case["job"]))
        actual.append(case["expected"])
        predicted.append(result.status)
        if result.status != case["expected"]:
            print(f"Mismatch: {case['name']} | expected {case['expected']} | got {result.status}")
    print(f"\nLabeled synthetic examples: {len(cases)}")
    print(classification_report(actual, predicted, labels=LABELS, digits=3, zero_division=0))
    print("Confusion matrix (rows expected, columns predicted):", ", ".join(LABELS))
    print(confusion_matrix(actual, predicted, labels=LABELS))
    print("Development examples are small, English-language, hand-labeled and non-independent. They do not measure recruiter decisions or ATS performance.")


if __name__ == "__main__":
    main()

