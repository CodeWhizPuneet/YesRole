import json
from types import SimpleNamespace

from app.schemas import Suggestion
from app.services import local_editor


def test_only_loopback_is_configurable(monkeypatch):
    monkeypatch.setenv("YESROLE_LLM_MODEL", "local-test")
    monkeypatch.setenv("YESROLE_LLM_URL", "https://external.example/v1")
    assert local_editor.settings() is None
    monkeypatch.setenv("YESROLE_LLM_URL", "http://127.0.0.1:11434/v1")
    assert local_editor.settings() == ("127.0.0.1", 11434, "local-test")


def test_ranker_returns_only_existing_rewrites(monkeypatch):
    recommendations = [
        Suggestion(id=name, kind="Safe Rephrasing", title=name, detail="Grounded.",
                   original="I built a " + name, replacement="Built a " + name)
        for name in ["dashboard", "report"]
    ]
    report = SimpleNamespace(suggestions=recommendations, findings=[])

    class Reply:
        status = 200

        def read(self, _size):
            return json.dumps({"choices": [{"message": {"content": '["report","invented","report","dashboard"]'}}]}).encode()

    class Connection:
        def __init__(self, *_args, **_kwargs):
            pass

        def request(self, method, path, **_kwargs):
            assert method == "POST" and path == "/v1/chat/completions"

        def getresponse(self):
            return Reply()

        def close(self):
            pass

    monkeypatch.setattr(local_editor, "settings", lambda: ("127.0.0.1", 11434, "test"))
    monkeypatch.setattr(local_editor.http.client, "HTTPConnection", Connection)
    assert local_editor.prioritize(report) == recommendations[::-1]

