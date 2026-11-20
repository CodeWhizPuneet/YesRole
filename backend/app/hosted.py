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

        # Health check — no auth required
        if path == "/healthz" and scope["method"] == "GET":
            await JSONResponse({"status": "ok"})(scope, receive, send)
            return

        # API routes — require Basic Auth, return JSON 401 (no WWW-Authenticate so browser won't pop up)
        if path == "/api" or path.startswith("/api/"):
            headers = dict(scope["headers"])
            scheme, _, token = headers.get(b"authorization", b"").partition(b" ")
            try:
                authorized = scheme.lower() == b"basic" and hmac.compare_digest(
                    base64.b64decode(token, validate=True), credentials
                )
            except binascii.Error:
                authorized = False
            if not authorized:
                await JSONResponse({"detail": "Unauthorized"}, status_code=401, headers={
                    "Cache-Control": "no-store",
                })(scope, receive, send)
                return
            await api(scope, receive, send)
            return

        # Static frontend files — no auth, React handles login
        try:
            await frontend(scope, receive, send)
        except HTTPException as error:
            await PlainTextResponse(error.detail, status_code=error.status_code)(scope, receive, send)

    return hosted


def create_default_app():
    configured_assets = os.getenv("YESROLE_WEB_ROOT")
    assets = Path(configured_assets) if configured_assets else Path(__file__).resolve().parents[2] / "frontend" / "dist"
    return create_app(assets, os.getenv("YESROLE_DEMO_PASSWORD", ""))

