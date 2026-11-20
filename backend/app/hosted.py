"""One-origin, password-protected demo entry point for the production build."""

import base64
import binascii
import hmac
import os
from pathlib import Path

from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.staticfiles import StaticFiles

from app.main import app as api


class Frontend(StaticFiles):
    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as error:
            if error.status_code != 404 or Path(path).suffix or "text/html" not in dict(scope["headers"]).get(b"accept", b"").decode("latin1"):
                raise
            return await super().get_response("index.html", scope)


def create_app(directory: Path, password: str):
    if len(password) < 16 or not password.isascii():
        raise RuntimeError("Set YESROLE_DEMO_PASSWORD to a strong ASCII password of at least 16 characters.")
    credentials = b"yesrole:" + password.encode("ascii")
    frontend = Frontend(directory=directory, html=True)

    async def hosted(scope, receive, send):
        if scope["type"] != "http":
            await api(scope, receive, send)
            return
        path = scope["path"]
        if path == "/healthz" and scope["method"] == "GET":
            await JSONResponse({"status": "ok"})(scope, receive, send)
            return
        headers = dict(scope["headers"])
        scheme, _, token = headers.get(b"authorization", b"").partition(b" ")
        try:
            authorized = scheme.lower() == b"basic" and hmac.compare_digest(
                base64.b64decode(token, validate=True), credentials
            )
        except binascii.Error:
            authorized = False
        if not authorized:
            await PlainTextResponse("Sign in to view the YesRole demo.", status_code=401, headers={
                "WWW-Authenticate": 'Basic realm="YesRole Demo"',
                "Cache-Control": "no-store",
            })(scope, receive, send)
            return

        async def private_response(message):
            if message["type"] == "http.response.start":
                response_headers = [(name, value) for name, value in message.get("headers", []) if name != b"cache-control"]
                message = {**message, "headers": [*response_headers, (b"cache-control", b"private, no-store")]}
            await send(message)

        if path == "/api" or path.startswith("/api/"):
            await api(scope, receive, private_response)
        else:
            try:
                await frontend(scope, receive, private_response)
            except HTTPException as error:
                await PlainTextResponse(error.detail, status_code=error.status_code)(scope, receive, private_response)

    return hosted


def create_default_app():
    configured_assets = os.getenv("YESROLE_WEB_ROOT")
    assets = Path(configured_assets) if configured_assets else Path(__file__).resolve().parents[2] / "frontend" / "dist"
    return create_app(assets, os.getenv("YESROLE_DEMO_PASSWORD", ""))

