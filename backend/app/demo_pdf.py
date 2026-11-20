from pathlib import Path

from app.services.export_service import export_pdf


if __name__ == "__main__":
    backend = Path(__file__).resolve().parents[1]
    text = (backend / "evaluation" / "demo-resume.txt").read_text(encoding="utf-8")
    destination = backend.parent / ".runtime" / "demo-resume.pdf"
    destination.parent.mkdir(exist_ok=True)
    destination.write_bytes(export_pdf(text))
    print(destination)

