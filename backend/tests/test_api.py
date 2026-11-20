import os

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import matching_engine
from app.services.embedding_service import similarities
from app.services.export_service import export_pdf

RESUME = "Alex Morgan\nSkills\nPython, pandas\nProjects\nI built a Python project to classify support tickets."
JOB = "Required qualifications:\n- Experience with Python.\n- Experience with Docker."


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("YESROLE_DB", str(tmp_path / "test.sqlite3"))
    return TestClient(app, base_url="http://127.0.0.1")


def test_validation_and_privacy(client):
    response = client.post("/api/match", json={"resume": "Private fragment"})
    assert response.status_code == 422
    assert "Private fragment" not in response.text
    assert client.post("/api/resume/parse", files={"file": ("bad.pdf", b"bad")}).status_code == 422
    assert client.post("/api/match", content=b"x" * (1600 * 1024 + 1)).status_code == 413
    assert client.post("/api/job/analyze", json={"description": JOB}, headers={"Origin": "https://example.test"}).status_code == 403
    assert client.get("/api/analyses", headers={"Host": "example.test"}).status_code == 400


def test_analysis_history_reanalysis_and_deletion(client, monkeypatch):
    # Orchestration fixture. The inference test below runs the actual model.
    monkeypatch.setattr(matching_engine, "similarities", lambda queries, rows: np.full((len(queries), len(rows)), .75))
    parsed = client.post("/api/resume/parse", files={"file": ("resume.pdf", export_pdf(RESUME))}).json()
    payload = {"title": "ML Intern", "description": JOB, "resume": parsed["text"], "source": parsed["source"]}
    response = client.post("/api/match", json=payload)
    assert response.status_code == 201
    original = response.json()
    assert [item["status"] for item in original["findings"]] == ["Supported", "Not Evidenced"]
    request = {"original_id": original["id"], "description": JOB, "resume": RESUME.replace("Python", "Java")}
    assert client.post("/api/resume/reanalyze", json={**request, "description": JOB + " Change."}).status_code == 422
    revised = client.post("/api/resume/reanalyze", json=request).json()
    assert revised["parent_id"] == original["id"]
    assert revised["score"] < original["score"]
    assert len(client.get("/api/analyses").json()) == 2
    assert client.post("/api/resume/export", json={"resume": request["resume"], "format": "docx"}).content.startswith(b"PK")
    assert client.delete("/api/analyses/" + original["id"]).status_code == 204
    assert client.get("/api/analyses/" + original["id"]).status_code == 404


@pytest.mark.skipif(os.getenv("YESROLE_TEST_MODEL") != "1", reason="Set YESROLE_TEST_MODEL=1 to run local model inference.")
def test_real_embeddings_and_match(client):
    matrix = similarities(["Build predictive models for customer attrition"], [
        "Trained a classifier to predict which customers would stop using the service.",
        "Edited photographs of flowers from the garden.",
    ])
    assert matrix.shape == (1, 2)
    assert -1 <= float(matrix.min()) <= float(matrix.max()) <= 1
    assert matrix[0, 0] > matrix[0, 1] + .15
    data = client.post("/api/match", json={"title": "ML Intern", "description": JOB, "resume": RESUME}).json()
    assert data["model"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert [item["status"] for item in data["findings"]] == ["Supported", "Not Evidenced"]

