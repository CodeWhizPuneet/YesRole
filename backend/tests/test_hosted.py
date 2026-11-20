import pytest
from fastapi.testclient import TestClient

from app.hosted import create_app


def test_hosted_login_and_routes(tmp_path, monkeypatch):
    assets = tmp_path / "web"
    assets.mkdir()
    (assets / "index.html").write_text("<title>YesRole</title>", encoding="utf-8")
    (assets / "app.js").write_text("console.log('YesRole')", encoding="utf-8")
    monkeypatch.setenv("YESROLE_DB", str(tmp_path / "test.sqlite3"))
    password = "fixture-password-2026"
    client = TestClient(create_app(assets, password), base_url="http://127.0.0.1")
    assert client.get("/healthz").status_code == 200
    assert client.get("/").status_code == 401
    assert client.get("/api/analyses", auth=("yesrole", "wrong")).status_code == 401
    assert client.get("/api/analyses", headers={"Authorization": "Basic !!!"}).status_code == 401

    login = ("yesrole", password)
    report = client.get("/analysis/example", auth=login, headers={"Accept": "text/html"})
    assert report.status_code == 200 and "YesRole" in report.text
    assert report.headers["cache-control"] == "private, no-store"
    assert client.get("/app.js", auth=login).status_code == 200
    assert client.get("/missing.js", auth=login, headers={"Accept": "text/html"}).status_code == 404
    assert client.get("/api/unknown", auth=login, headers={"Accept": "text/html"}).status_code == 404
    assert client.get("/api/analyses", auth=login).json() == []


def test_hosted_startup_requires_password(tmp_path):
    with pytest.raises(RuntimeError, match="YESROLE_DEMO_PASSWORD"):
        create_app(tmp_path, "")

