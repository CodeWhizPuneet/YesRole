import os
from pathlib import Path

from huggingface_hub import snapshot_download

from app.services.embedding_service import MODEL_ID, MODEL_REVISION


def main() -> None:
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    destination = Path(__file__).resolve().parents[2] / ".runtime" / "minilm"
    snapshot_download(
        MODEL_ID,
        revision=MODEL_REVISION,
        local_dir=destination,
        allow_patterns=["*.json", "vocab.txt", "model.safetensors"],
        ignore_patterns=["onnx/*", "openvino/*"],
    )
    print(f"Model downloaded to {destination}")


if __name__ == "__main__":
    main()

