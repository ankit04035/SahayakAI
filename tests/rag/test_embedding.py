"""
Comprehensive Tests for Transformer / Sentence-Embedding Layer (Step 6).
Covers configuration, model manager lifecycle, embedding generation (single, batch, query),
multilingual support (English, Hindi, Hinglish), vector validation/serialization,
and database persistence into DocumentChunk.
"""

import math
from unittest.mock import patch
import pytest
from sqlalchemy.orm import Session

from backend.app.config import Settings, get_settings
from backend.app.database import SessionLocal
from backend.app.exceptions import AppException
from backend.app.models.document import Document, DocumentChunk
from backend.app.models.user import User
from backend.app.rag.embedding_service import (
    embed_batch,
    embed_document_chunks,
    embed_query,
    embed_text,
    get_embedding_dimension,
)
from backend.app.rag.exceptions import (
    EmbeddingModelLoadError,
    EmbeddingPersistenceError,
    EmbeddingValidationError,
)
from backend.app.rag.model_manager import EmbeddingModelManager, get_model_manager
from backend.app.rag.vector_utils import (
    deserialize_vector,
    serialize_vector,
    validate_vector,
)


@pytest.fixture
def db_session():
    """Provide an isolated database session with rollback/cleanup."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def shared_model():
    """Ensure the sentence transformer model is loaded once for the test module."""
    manager = get_model_manager()
    return manager.load_model()


# ==============================================================================
# GROUP A: CONFIGURATION TESTS
# ==============================================================================

def test_default_embedding_configuration():
    """Verify default model name, dimension, device, and batch size."""
    settings = get_settings()
    assert settings.EMBEDDING_MODEL == "all-MiniLM-L6-v2"
    assert settings.EMBEDDING_DIMENSION == 384
    assert settings.EMBEDDING_DEVICE in {"cpu", "cuda"}
    assert settings.EMBEDDING_BATCH_SIZE == 32
    assert settings.EMBEDDING_NORMALIZE is True


def test_custom_embedding_settings_validation():
    """Verify settings validation rejects invalid embedding dimension or batch size."""
    with pytest.raises(ValueError):
        Settings(EMBEDDING_DIMENSION=0)

    with pytest.raises(ValueError):
        Settings(EMBEDDING_BATCH_SIZE=-5)


# ==============================================================================
# GROUP B: EMBEDDING SERVICE TESTS (REAL all-MiniLM-L6-v2 MODEL)
# ==============================================================================

def test_model_loads_successfully(shared_model):
    """Verify SentenceTransformer model loads and reports correct dimension."""
    manager = get_model_manager()
    assert manager.is_loaded() is True
    metadata = manager.get_metadata()
    assert metadata["model_name"] == "all-MiniLM-L6-v2"
    assert metadata["dimension"] == 384


def test_model_reused_in_process():
    """Verify consecutive load_model calls reuse the cached instance in-memory."""
    manager = get_model_manager()
    model_a = manager.load_model()
    model_b = manager.load_model()
    assert model_a is model_b


def test_same_text_produces_consistent_embedding(shared_model):
    """Verify deterministic embeddings for identical inputs."""
    text = "Supervised machine learning algorithms require training data."
    emb_1 = embed_text(text)
    emb_2 = embed_text(text)
    assert len(emb_1) == 384
    assert len(emb_2) == 384
    # Exact or near-exact floating point equality
    for v1, v2 in zip(emb_1, emb_2):
        assert math.isclose(v1, v2, abs_tol=1e-5)


def test_embedding_dimension_exact_384(shared_model):
    """Verify embedding dimension matches 384."""
    text = "Deep neural networks for natural language processing."
    emb = embed_text(text)
    assert len(emb) == 384
    assert get_embedding_dimension() == 384


def test_embedding_is_l2_normalized(shared_model):
    """Verify vectors are L2-normalized to unit norm (~1.0) for cosine similarity."""
    text = "Support Vector Machines and decision trees for classification."
    emb = embed_text(text)
    norm = math.sqrt(sum(x * x for x in emb))
    assert math.isclose(norm, 1.0, abs_tol=1e-3)


def test_query_embedding_works(shared_model):
    """Verify query embedding generates valid 384-dim vector."""
    query = "What is the role of gradient descent in optimization?"
    emb = embed_query(query)
    assert len(emb) == 384
    assert all(isinstance(x, float) for x in emb)


def test_batch_embedding_works(shared_model):
    """Verify batch processing produces vector collection matching input length."""
    texts = [
        "First academic paragraph on sorting algorithms.",
        "Second academic paragraph on binary search trees.",
        "Third academic paragraph on graph traversal.",
    ]
    vectors = embed_batch(texts, batch_size=2)
    assert len(vectors) == 3
    for vec in vectors:
        assert len(vec) == 384
        assert all(isinstance(x, float) for x in vec)


def test_empty_text_handled_correctly():
    """Verify empty or whitespace-only text raises EmbeddingValidationError."""
    with pytest.raises(EmbeddingValidationError):
        embed_text("")

    with pytest.raises(EmbeddingValidationError):
        embed_text("   \n\t  ")

    with pytest.raises(EmbeddingValidationError):
        embed_query("")


def test_empty_batch_handled_correctly():
    """Verify empty input list returns empty result without errors."""
    assert embed_batch([]) == []


def test_english_text_works(shared_model):
    """Verify embedding generation on standard academic English."""
    english = "Object-oriented programming principles include encapsulation, inheritance, and polymorphism."
    emb = embed_text(english)
    assert len(emb) == 384


def test_hindi_text_works_without_crashing(shared_model):
    """Verify Devanagari Hindi text generates valid 384-dimensional embeddings."""
    hindi = "मशीन लर्निंग और डेटा साइंस की मूलभूत अवधारणाएं परीक्षा की दृष्टि से अत्यंत महत्वपूर्ण हैं।"
    emb = embed_text(hindi)
    assert len(emb) == 384
    assert all(isinstance(x, float) for x in emb)


def test_hinglish_text_works_without_crashing(shared_model):
    """Verify Romanized Hinglish text generates valid 384-dimensional embeddings."""
    hinglish = "Yeh machine learning syllabus cover karna semester exam ke liye bahut zaroori hai."
    emb = embed_text(hinglish)
    assert len(emb) == 384
    assert all(isinstance(x, float) for x in emb)


# ==============================================================================
# GROUP C: VECTOR VALIDATION & SERIALIZATION TESTS
# ==============================================================================

def test_vector_serialization_and_deserialization():
    """Verify vector serialization to list and deserialization roundtrip."""
    original_vector = [0.123456, -0.654321, 0.0] * 128  # 384 elements
    serialized = serialize_vector(original_vector, expected_dim=384)
    assert isinstance(serialized, list)
    assert len(serialized) == 384

    deserialized = deserialize_vector(serialized, expected_dim=384)
    assert deserialized == serialized


def test_corrupted_vector_rejected_wrong_dim():
    """Verify vectors with incorrect dimensionality are rejected."""
    short_vec = [0.1] * 100
    with pytest.raises(EmbeddingValidationError):
        validate_vector(short_vec, expected_dim=384)

    long_vec = [0.1] * 500
    with pytest.raises(EmbeddingValidationError):
        validate_vector(long_vec, expected_dim=384)


def test_corrupted_vector_rejected_nan_inf():
    """Verify vectors containing NaN or Inf are rejected."""
    nan_vec = [0.1] * 383 + [float("nan")]
    with pytest.raises(EmbeddingValidationError):
        validate_vector(nan_vec, expected_dim=384)

    inf_vec = [0.1] * 383 + [float("inf")]
    with pytest.raises(EmbeddingValidationError):
        validate_vector(inf_vec, expected_dim=384)


def test_corrupted_vector_rejected_non_numeric():
    """Verify vectors containing non-numeric types are rejected."""
    bad_vec = [0.1] * 383 + ["string_element"]
    with pytest.raises(EmbeddingValidationError):
        validate_vector(bad_vec, expected_dim=384)


def test_no_pickle_used():
    """Verify vector is serialized as standard JSON/numeric sequence, not pickle."""
    vector = [0.5] * 384
    serialized = serialize_vector(vector, expected_dim=384)
    assert isinstance(serialized, list)
    assert all(isinstance(x, float) for x in serialized)


# ==============================================================================
# GROUP D: DATABASE INTEGRATION TESTS
# ==============================================================================

def test_existing_chunks_without_embeddings_remain_valid(db_session: Session):
    """Verify existing chunks with embedding=None remain valid."""
    # Ensure default user exists
    user = db_session.query(User).filter(User.email == "default@sahayakai.local").first()
    if not user:
        user = User(email="default@sahayakai.local", name="Default User")
        db_session.add(user)
        db_session.commit()

    doc = Document(
        user_id=user.id,
        title="Test Document",
        original_filename="test.txt",
        stored_filename="test_stored.txt",
        file_type=".txt",
        file_size=100,
        processing_status="completed",
    )
    db_session.add(doc)
    db_session.commit()

    chunk = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        content="Existing chunk content without vector.",
        character_count=38,
        embedding=None,
    )
    db_session.add(chunk)
    db_session.commit()

    # Query back
    fetched = db_session.query(DocumentChunk).filter(DocumentChunk.id == chunk.id).first()
    assert fetched.embedding is None
    assert fetched.content == "Existing chunk content without vector."


def test_embed_document_chunks_persists_to_database(db_session: Session, shared_model):
    """Verify end-to-end embedding generation and persistence for document chunks."""
    user = db_session.query(User).filter(User.email == "default@sahayakai.local").first()
    if not user:
        user = User(email="default@sahayakai.local", name="Default User")
        db_session.add(user)
        db_session.commit()

    doc = Document(
        user_id=user.id,
        title="DSA Textbook",
        original_filename="dsa.txt",
        stored_filename="dsa_stored.txt",
        file_type=".txt",
        file_size=200,
        processing_status="completed",
    )
    db_session.add(doc)
    db_session.commit()

    chunk1 = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        content="Arrays and linked lists are foundational linear data structures.",
        character_count=65,
        embedding=None,
    )
    chunk2 = DocumentChunk(
        document_id=doc.id,
        chunk_index=1,
        content="Trees and graphs represent hierarchical and networked relationships.",
        character_count=68,
        embedding=None,
    )
    db_session.add_all([chunk1, chunk2])
    db_session.commit()

    # Generate and persist embeddings
    count = embed_document_chunks(doc.id, db_session, batch_size=2)
    assert count == 2

    # Verify both chunks have 384-dimensional embeddings stored
    refreshed_1 = db_session.query(DocumentChunk).filter(DocumentChunk.id == chunk1.id).first()
    refreshed_2 = db_session.query(DocumentChunk).filter(DocumentChunk.id == chunk2.id).first()

    assert refreshed_1.embedding is not None
    assert refreshed_2.embedding is not None
    assert len(refreshed_1.embedding) == 384
    assert len(refreshed_2.embedding) == 384
    assert all(isinstance(x, float) for x in refreshed_1.embedding)


def test_embed_document_chunks_not_found(db_session: Session):
    """Verify 404 is raised for non-existent document."""
    with pytest.raises(AppException) as exc:
        embed_document_chunks(999999, db_session)
    assert exc.value.error_code == "DOCUMENT_NOT_FOUND"
    assert exc.value.status_code == 404


def test_embed_document_chunks_transaction_safety(db_session: Session):
    """Verify database rollback when batch encoding or persistence fails."""
    user = db_session.query(User).filter(User.email == "default@sahayakai.local").first()
    if not user:
        user = User(email="default@sahayakai.local", name="Default User")
        db_session.add(user)
        db_session.commit()

    doc = Document(
        user_id=user.id,
        title="Failing Doc",
        original_filename="fail.txt",
        stored_filename="fail_stored.txt",
        file_type=".txt",
        file_size=50,
        processing_status="completed",
    )
    db_session.add(doc)
    db_session.commit()

    chunk = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        content="Normal chunk text.",
        character_count=18,
        embedding=None,
    )
    db_session.add(chunk)
    db_session.commit()

    # Simulate failure in embed_batch
    with patch("backend.app.rag.embedding_service.embed_batch", side_effect=RuntimeError("Simulated batch failure")):
        with pytest.raises(EmbeddingPersistenceError):
            embed_document_chunks(doc.id, db_session)

    # Verify chunk embedding remains None (transaction rolled back safely)
    refreshed = db_session.query(DocumentChunk).filter(DocumentChunk.id == chunk.id).first()
    assert refreshed.embedding is None


# ==============================================================================
# GROUP E: MODEL LOADING AND ERROR HANDLING TESTS
# ==============================================================================

def test_model_loading_failure_handled():
    """Verify model loading errors are mapped to EmbeddingModelLoadError."""
    with patch("backend.app.rag.model_manager.SentenceTransformer", side_effect=RuntimeError("Download failed")):
        manager = EmbeddingModelManager()
        with pytest.raises(EmbeddingModelLoadError) as exc:
            manager.load_model(force_reload=True)
        assert exc.value.error_code == "EMBEDDING_MODEL_LOAD_ERROR"
        assert exc.value.status_code == 503
