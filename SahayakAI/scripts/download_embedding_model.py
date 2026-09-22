"""
Pre-download and verify the SentenceTransformer embedding model.
Validates model initialization, embedding generation, and dimension correctness.
Exits 0 on success, non-zero on failure.
"""

import os
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from backend.app.config import get_settings
    from backend.app.rag.model_manager import get_model_manager
    from backend.app.rag.embedding_service import embed_text
except ImportError as err:
    print(f"ERROR: Import failed. Ensure PYTHONPATH includes project root: {err}", file=sys.stderr)
    sys.exit(1)


def main() -> int:
    settings = get_settings()
    print("=" * 65)
    print("SahayakAI — Sentence Transformer Model Setup & Verification")
    print("=" * 65)
    print(f"Configured Model     : {settings.EMBEDDING_MODEL}")
    print(f"Expected Dimension   : {settings.EMBEDDING_DIMENSION}")
    print(f"Configured Device    : {settings.EMBEDDING_DEVICE}")
    print(f"Normalization        : {settings.EMBEDDING_NORMALIZE}")
    print("-" * 65)
    print("Initializing and loading embedding model...")

    start_time = time.time()
    try:
        manager = get_model_manager()
        model = manager.load_model()
        load_duration = time.time() - start_time
        print(f"Model loaded successfully in {load_duration:.2f} seconds.")

        # Verify dimension
        if hasattr(model, "get_embedding_dimension"):
            dim = model.get_embedding_dimension()
        else:
            dim = model.get_sentence_embedding_dimension()
        print(f"Verified Model Dimension: {dim}")
        if dim != settings.EMBEDDING_DIMENSION:
            print(
                f"ERROR: Dimension mismatch! Expected {settings.EMBEDDING_DIMENSION}, got {dim}",
                file=sys.stderr,
            )
            return 1

        # Run sample inference
        sample_text = "SahayakAI is an offline-capable academic mentorship assistant."
        print(f"Generating test embedding for: '{sample_text}'")
        emb_start = time.time()
        embedding = embed_text(sample_text)
        emb_duration = time.time() - emb_start

        print(f"Embedding generated in {emb_duration * 1000:.1f} ms.")
        print(f"Generated Vector Length : {len(embedding)}")
        print(f"Sample Vector Values    : [{embedding[0]:.4f}, {embedding[1]:.4f}, ..., {embedding[-1]:.4f}]")
        print("-" * 65)
        print("STATUS: SUCCESS — Embedding model is verified and ready for RAG operations.")
        print("=" * 65)
        return 0

    except Exception as exc:
        print(f"ERROR: Model setup and verification failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
