import os
from pathlib import Path
from threading import Lock

import numpy as np
from dotenv import load_dotenv


MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
ROOT = Path(__file__).resolve().parents[3]
LOCAL_CACHE = ROOT / ".runtime" / "minilm"
load_dotenv(ROOT / ".env")
CACHE_LOCK = Lock()
_model = None


class ModelUnavailable(RuntimeError):
    pass


def model():
    global _model
    with CACHE_LOCK:
        if _model is None:
            try:
                from sentence_transformers import SentenceTransformer
                location = os.getenv("YESROLE_MODEL_PATH") or (
                    str(LOCAL_CACHE) if (LOCAL_CACHE / "model.safetensors").is_file() else MODEL_ID
                )
                _model = SentenceTransformer(
                    location,
                    device="cpu",
                    revision=MODEL_REVISION if location == MODEL_ID else None,
                    local_files_only=os.getenv("YESROLE_OFFLINE", "").lower() == "true",
                    trust_remote_code=False,
                    model_kwargs={"use_safetensors": True},
                )
            except Exception:
                raise ModelUnavailable(
                    "Could not load all-MiniLM-L6-v2. Check the model cache or set YESROLE_MODEL_PATH to a local copy. "
                    "See the model setup instructions in the README."
                ) from None
        return _model


def similarities(queries: list[str], passages: list[str]) -> np.ndarray:
    encoder = model()
    try:
        vectors = encoder.encode(queries + passages, batch_size=32, normalize_embeddings=True,
                                 convert_to_numpy=True, show_progress_bar=False)
        return np.clip(vectors[:len(queries)] @ vectors[len(queries):].T, -1, 1)
    except Exception:
        raise ModelUnavailable("The embedding model could not process this input. Retry with a shorter document.") from None


if __name__ == "__main__":
    print(f"Ready: {MODEL_ID}, embedding dimensions: {model().get_sentence_embedding_dimension()}")

