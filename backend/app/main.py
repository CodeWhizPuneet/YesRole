import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app import storage
from app.schemas import (
    Analysis, AnalysisSummary, ExportInput, InputError, JobInput, MatchInput, ParsedResume,
    Requirement, ResumeInput, RevisionInput, Suggestion,
)
from app.services import ats_checker, document_parser, export_service, job_parser, local_editor, optimization_engine
from app.services.embedding_service import MODEL_ID, ModelUnavailable
from app.services.matching_engine import match
from app.services.scoring_engine import score

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
ORIGINS = os.getenv("YESROLE_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
ORIGINS = [origin.strip() for origin in ORIGINS if origin.strip() and origin.strip() != "*"]
HOSTS = [host.strip() for host in os.getenv("YESROLE_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if host.strip()]


class LocalRequestLimits:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "DELETE"}:
            await self.app(scope, receive, send)
            return
        headers = dict(scope["headers"])
        origin = headers.get(b"origin")
        if origin and origin.decode("latin1") not in ORIGINS:
            await JSONResponse({"detail": "This origin cannot modify local YesRole data."}, status_code=403)(scope, receive, send)
            return
        if scope["method"] == "DELETE":
            await self.app(scope, receive, send)
            return
        limit = document_parser.MAX_FILE + 64 * 1024 if scope["path"] == "/api/resume/parse" else 1600 * 1024
        buffer = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(buffer) + len(chunk) > limit:
                await JSONResponse({"detail": "The request exceeds the upload size limit."}, status_code=413)(scope, receive, send)
                return
            buffer.extend(chunk)
            if not message.get("more_body"):
                break

        sent = False

        async def replay():
            nonlocal sent
            if sent:
                return await receive()
            sent = True
            body = bytes(buffer)
            buffer.clear()
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, replay, send)


app = FastAPI(title="YesRole API", version="1.0")
app.add_middleware(LocalRequestLimits)
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_methods=["GET", "POST", "DELETE"],
                   allow_headers=["Content-Type"])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=HOSTS)


@app.exception_handler(InputError)
async def invalid_input(_request: Request, exc: InputError):
    return JSONResponse({"detail": str(exc)}, status_code=422)


@app.exception_handler(RequestValidationError)
async def invalid_request(_request: Request, exc: RequestValidationError):
    errors = [{"field": ".".join(str(loc) for loc in item["loc"][1:]), "message": item["msg"]}
              for item in exc.errors()]
    return JSONResponse({"detail": "Check the required fields and text limits.", "errors": errors}, status_code=422)


@app.exception_handler(ModelUnavailable)
async def model_unavailable(_request: Request, exc: ModelUnavailable):
    return JSONResponse({"detail": str(exc)}, status_code=503)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "model": MODEL_ID, "mode": "local"}


@app.get("/api/capabilities")
def capabilities() -> dict[str, bool]:
    return {"local_editor": local_editor.settings() is not None}


@app.post("/api/resume/parse", response_model=ParsedResume)
def parse_upload(file: UploadFile = File(...)):
    return document_parser.parse_file(file.filename or "", file.file.read(document_parser.MAX_FILE + 1))


@app.post("/api/resume/parse-text", response_model=ParsedResume)
def parse_text(payload: ResumeInput):
    return document_parser.parse_text(payload.resume)


@app.post("/api/job/analyze", response_model=list[Requirement])
def analyze_job(payload: JobInput):
    return job_parser.parse_job(payload.description)


def report(payload: MatchInput, parent_id: str | None = None) -> Analysis:
    parsed = document_parser.parse_text(payload.resume, payload.source, payload.warnings)
    requirements = job_parser.parse_job(payload.description)
    findings = match(parsed, requirements)
    overall, dimensions = score(findings)
    analysis = Analysis(
        id=str(uuid4()), created_at=datetime.now(timezone.utc).isoformat(),
        title=payload.title, company=payload.company, version=payload.version, score=overall,
        dimensions=dimensions, findings=findings, ats=ats_checker.check(parsed),
        suggestions=optimization_engine.recommend(parsed, findings), model=MODEL_ID, parent_id=parent_id,
    )
    storage.save(analysis, hashlib.sha256(payload.description.encode()).hexdigest())
    return analysis


@app.post("/api/match", response_model=Analysis, status_code=201)
def analyze(payload: MatchInput):
    return report(payload)


@app.post("/api/resume/reanalyze", response_model=Analysis, status_code=201)
def reanalyze(payload: RevisionInput):
    original, digest = get_saved(payload.original_id)
    if digest != hashlib.sha256(payload.description.encode()).hexdigest():
        raise InputError("Reanalysis requires the same job description. Start a new analysis for a different role.")
    return report(MatchInput(resume=payload.resume, description=payload.description, title=original.title,
                             company=original.company, version=payload.version), original.id)


@app.get("/api/analyses", response_model=list[AnalysisSummary])
def history():
    return storage.list_reports()


def get_saved(analysis_id: str):
    saved = storage.read(analysis_id)
    if saved is None:
        raise HTTPException(404, "This analysis could not be found.")
    return saved


@app.get("/api/analyses/{analysis_id}", response_model=Analysis)
def get_report(analysis_id: str):
    return get_saved(analysis_id)[0]


@app.get("/api/analyses/{analysis_id}/suggestions", response_model=list[Suggestion])
def get_suggestions(analysis_id: str):
    return get_saved(analysis_id)[0].suggestions


@app.post("/api/resume/optimize/{analysis_id}", response_model=list[Suggestion])
def prioritize_suggestions(analysis_id: str):
    ordered = local_editor.prioritize(get_saved(analysis_id)[0])
    if ordered is None:
        raise HTTPException(503, "The optional local assistant is unavailable. Your grounded suggestions are still available.")
    return ordered


@app.delete("/api/analyses/{analysis_id}", status_code=204)
def delete_report(analysis_id: str):
    if not storage.delete(analysis_id):
        raise HTTPException(404, "This analysis could not be found.")
    return Response(status_code=204)


@app.post("/api/resume/export")
def export(payload: ExportInput):
    text = document_parser.parse_text(payload.resume).text
    if payload.format == "docx":
        content = export_service.export_docx(text)
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        content = export_service.export_pdf(text)
        mime = "application/pdf"
    return Response(content, media_type=mime, headers={
        "Content-Disposition": f'attachment; filename="yesrole-resume.{payload.format}"',
        "Cache-Control": "no-store",
    })

