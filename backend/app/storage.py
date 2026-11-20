import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from app.schemas import Analysis, AnalysisSummary

DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "yesrole.sqlite3"


@contextmanager
def connection():
    path = Path(os.getenv("YESROLE_DB") or DEFAULT_DB)
    path.parent.mkdir(parents=True, exist_ok=True)
    database = sqlite3.connect(path, timeout=10)
    try:
        database.execute("""CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY, created_at TEXT NOT NULL, body TEXT NOT NULL,
            job_digest TEXT NOT NULL, parent_id TEXT, score INTEGER NOT NULL
        )""")
        database.execute("PRAGMA secure_delete=ON")
        yield database
    finally:
        database.close()


def save(analysis: Analysis, digest: str) -> None:
    with connection() as database:
        database.execute(
            "INSERT INTO reports VALUES (?, ?, ?, ?, ?, ?)",
            (analysis.id, analysis.created_at, analysis.model_dump_json(), digest, analysis.parent_id, analysis.score),
        )
        database.commit()


def read(analysis_id: str) -> tuple[Analysis, str] | None:
    with connection() as database:
        row = database.execute("SELECT body, job_digest FROM reports WHERE id = ?", (analysis_id,)).fetchone()
    return (Analysis.model_validate_json(row[0]), row[1]) if row else None


def list_reports() -> list[AnalysisSummary]:
    with connection() as database:
        rows = database.execute("""
            SELECT r.body, p.score FROM reports r LEFT JOIN reports p ON r.parent_id = p.id
            ORDER BY r.created_at DESC
        """).fetchall()
    result = []
    for body, baseline in rows:
        item = Analysis.model_validate_json(body)
        result.append(AnalysisSummary(
            id=item.id, created_at=item.created_at, title=item.title, company=item.company,
            version=item.version, score=item.score, supported=sum(f.status == "Supported" for f in item.findings),
            total=len(item.findings), parent_id=item.parent_id, change=item.score - baseline if baseline is not None else None,
        ))
    return result


def delete(analysis_id: str) -> bool:
    with connection() as database:
        cursor = database.execute("DELETE FROM reports WHERE id = ?", (analysis_id,))
        database.commit()
        return bool(cursor.rowcount)

