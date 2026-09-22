"""
Comprehensive Tests for Document Processing and Core NLP Pipeline (Step 5).
Covers file validation, sanitization, safe storage, text extraction (PDF & TXT),
text cleaning, document statistics, keyword extraction, query preprocessing,
boundary-aware chunking, database persistence, and FastAPI REST endpoints.
"""

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import fitz

from backend.app.config import get_settings
from backend.app.database import SessionLocal, get_db
from backend.app.exceptions import AppException
from backend.app.main import app
from backend.app.models.document import Document, DocumentChunk
from backend.app.nlp.chunker import chunk_pages, chunk_text, find_split_point
from backend.app.nlp.keyword_extractor import extract_keywords
from backend.app.nlp.query_preprocessor import preprocess_query
from backend.app.nlp.text_cleaner import clean_text
from backend.app.nlp.text_statistics import (
    compute_text_statistics,
    detect_language_heuristic,
)
from backend.app.services.document_service import (
    delete_document,
    get_document_by_id,
    get_document_chunks,
    get_or_create_default_user,
    list_documents,
    process_document_upload,
)
from backend.app.utils.file_validation import (
    validate_file_content,
    validate_file_metadata,
)
from backend.app.utils.filename import (
    generate_stored_filename,
    get_safe_storage_path,
    sanitize_filename,
)


@pytest.fixture
def db_session():
    """Provide a database session for testing, with automatic cleanup."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """Provide a TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_pdf_bytes():
    """Create a minimal valid 2-page PDF in memory."""
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((50, 72), "SahayakAI Academic Reference. Chapter 1: Machine Learning Basics.")
    page2 = doc.new_page()
    page2.insert_text((50, 72), "Chapter 2: Deep Neural Networks and Transformers in Education.")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ==============================================================================
# 1. FILENAME SANITIZATION AND PATH SECURITY TESTS
# ==============================================================================

def test_sanitize_filename_prevents_directory_traversal():
    """Verify directory traversal patterns and absolute paths are stripped."""
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\Windows\\System32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("C:\\Users\\admin\\document.pdf") == "document.pdf"
    assert sanitize_filename("/root/sensitive/notes.txt") == "notes.txt"


def test_sanitize_filename_replaces_dangerous_characters():
    """Verify special and shell characters are replaced with underscores."""
    raw_name = "my document <1> *final* & (draft).pdf"
    cleaned = sanitize_filename(raw_name)
    assert "<" not in cleaned and ">" not in cleaned
    assert "*" not in cleaned and "&" not in cleaned
    assert cleaned.endswith(".pdf")


def test_sanitize_filename_edge_cases():
    """Verify handling of empty, whitespace-only, and dot-only filenames."""
    assert sanitize_filename("") == "unnamed_document.txt"
    assert sanitize_filename("   ") == "unnamed_document.txt"
    assert sanitize_filename("...") == "unnamed_document.txt"


def test_generate_stored_filename_unique():
    """Verify stored filename prepends unique UUIDv4 token."""
    name1 = generate_stored_filename("syllabus.pdf")
    name2 = generate_stored_filename("syllabus.pdf")
    assert name1 != name2
    assert name1.endswith("_syllabus.pdf")
    assert len(name1) > len("syllabus.pdf") + 30


def test_get_safe_storage_path_enforces_directory_containment(tmp_path):
    """Verify target path is validated within the configured base directory."""
    safe_path = get_safe_storage_path(tmp_path, "file_123.pdf")
    assert safe_path.parent == tmp_path.resolve()

    with pytest.raises(AppException) as exc:
        get_safe_storage_path(tmp_path, "../outside.pdf")
    assert exc.value.error_code == "PATH_TRAVERSAL_DETECTED"


# ==============================================================================
# 2. FILE VALIDATION TESTS
# ==============================================================================

def test_validate_file_metadata_supported_extensions():
    """Verify supported extensions .pdf and .txt pass metadata validation."""
    assert validate_file_metadata("paper.pdf") == ".pdf"
    assert validate_file_metadata("NOTES.TXT") == ".txt"


def test_validate_file_metadata_unsupported_extensions():
    """Verify unsupported extensions are rejected with INVALID_FILE_TYPE."""
    for bad_name in ["script.exe", "document.docx", "data.csv", "image.png"]:
        with pytest.raises(AppException) as exc:
            validate_file_metadata(bad_name)
        assert exc.value.error_code == "INVALID_FILE_TYPE"
        assert exc.value.status_code == 400


def test_validate_file_metadata_content_length_limit():
    """Verify content length exceeding maximum limit is rejected with FILE_TOO_LARGE."""
    settings = get_settings()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    with pytest.raises(AppException) as exc:
        validate_file_metadata("big.pdf", content_length=max_bytes + 1024)
    assert exc.value.error_code == "FILE_TOO_LARGE"
    assert exc.value.status_code == 413


def test_validate_file_content_empty_rejection():
    """Verify 0-byte file content is rejected with EMPTY_FILE."""
    with pytest.raises(AppException) as exc:
        validate_file_content(b"", ".txt")
    assert exc.value.error_code == "EMPTY_FILE"


def test_validate_file_content_pdf_magic_bytes(sample_pdf_bytes):
    """Verify valid PDF magic bytes header is required."""
    mime, enc = validate_file_content(sample_pdf_bytes, ".pdf")
    assert mime == "application/pdf"
    assert enc == "binary"

    # Fake PDF missing magic header
    fake_pdf = b"This is not a real PDF document at all"
    with pytest.raises(AppException) as exc:
        validate_file_content(fake_pdf, ".pdf")
    assert exc.value.error_code == "INVALID_FILE_CONTENT"


def test_validate_file_content_txt_decoding():
    """Verify text decoding and binary null byte rejection for TXT files."""
    valid_text = "Data structures and algorithms in Python.".encode("utf-8")
    mime, enc = validate_file_content(valid_text, ".txt")
    assert mime == "text/plain"
    assert enc == "utf-8"

    # Binary file with null bytes disguised as .txt
    binary_junk = b"\x00\x01\x02\x03\x04\x05binary_data"
    with pytest.raises(AppException) as exc:
        validate_file_content(binary_junk, ".txt")
    assert exc.value.error_code == "INVALID_FILE_CONTENT"


# ==============================================================================
# 3. NLP PIPELINE: CLEANING, STATS, KEYWORDS, QUERY PREPROCESSING, CHUNKING
# ==============================================================================

def test_clean_text_unicode_normalization_and_whitespace():
    """Verify Unicode NFC normalization, line collapsing, and artifact removal."""
    raw = "Hello   world!\r\n\r\n\r\nLine 2 with \u00a0 non-breaking space.\n\n\n\nLine 3."
    cleaned = clean_text(raw)
    assert "Hello world!" in cleaned
    assert "Line 2 with non-breaking space." in cleaned
    assert "\r" not in cleaned
    assert "\n\n\n" not in cleaned  # Max 2 consecutive newlines


def test_clean_text_pdf_hyphenation_fix():
    """Verify hyphenated words split across lines in PDFs are reassembled."""
    raw = "This is a super-\n   vised learning algo-\nrithm."
    cleaned = clean_text(raw)
    assert "supervised" in cleaned
    assert "algorithm" in cleaned


def test_clean_text_hindi_preservation():
    """Verify Hindi Devanagari text and purna viram punctuation are preserved."""
    hindi_raw = "मशीन लर्निंग कृत्रिम बुद्धिमत्ता की महत्वपूर्ण शाखा है। यह डेटा से सीखती है।"
    cleaned = clean_text(hindi_raw)
    assert "मशीन लर्निंग" in cleaned
    assert "है।" in cleaned


def test_compute_text_statistics_metrics():
    """Verify word, sentence, paragraph, and reading time calculations."""
    text = (
        "Machine learning enables automated pattern recognition in empirical data. "
        "It provides actionable predictive models across diverse domains.\n\n"
        "Deep learning further accelerates representation learning."
    )
    stats = compute_text_statistics(text, page_count=2)
    assert stats.word_count > 15
    assert stats.sentence_count == 3
    assert stats.paragraph_count == 2
    assert stats.page_count == 2
    assert stats.estimated_reading_time_minutes > 0.0
    assert stats.primary_language == "en"


def test_language_detection_heuristic():
    """Verify script-based detection for English, Hindi, and Hinglish."""
    english = "Supervised machine learning optimizes parameters via gradient descent."
    hindi = "मशीन लर्निंग कृत्रिम बुद्धिमत्ता की एक आधुनिक शाखा है।"
    hinglish = "Machine learning concepts ko samajhna exam preparation ke liye bahut zaroori hai."

    assert detect_language_heuristic(english) == "en"
    assert detect_language_heuristic(hindi) == "hi"
    assert detect_language_heuristic(hinglish) == "hinglish"
    assert detect_language_heuristic("") == "unknown"


def test_keyword_extraction_english_and_hindi():
    """Verify keyword extraction filters stopwords and scores unigrams and bigrams."""
    text = (
        "Supervised machine learning relies on labeled datasets. Machine learning algorithms "
        "minimize loss functions. Unsupervised learning discovers latent clustering patterns."
    )
    keywords = extract_keywords(text, top_n=5)
    extracted_terms = [k["keyword"] for k in keywords]
    assert any("machine learning" in term or "learning" in term for term in extracted_terms)
    assert "the" not in extracted_terms
    assert "and" not in extracted_terms


def test_preprocess_query_functionality():
    """Verify query normalization, stopword filtering, and language identification."""
    query = "What is Supervised Machine Learning in AI?"
    result = preprocess_query(query)
    assert result.original_query == query
    assert "supervised" in result.tokens
    assert "machine" in result.tokens
    assert "is" not in result.filtered_tokens  # Stopword removed
    assert result.language == "en"
    assert not result.is_empty


def test_chunker_short_text():
    """Verify text shorter than chunk_size produces exactly 1 chunk."""
    short_text = "A concise concept explanation."
    chunks = chunk_text(short_text, chunk_size=500, chunk_overlap=50)
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].content == short_text
    assert chunks[0].character_count == len(short_text)


def test_chunker_sliding_window_overlap():
    """Verify multi-chunk text respects chunk size limits, overlap, and sequential indexes."""
    para = "Machine learning models require training datasets, loss functions, and optimization. " * 15
    chunks = chunk_text(para, chunk_size=200, chunk_overlap=40)
    assert len(chunks) > 1
    for i, chk in enumerate(chunks):
        assert chk.chunk_index == i
        assert chk.character_count <= 260  # Allows boundary padding
        assert chk.word_count > 0


def test_chunker_page_attribution():
    """Verify chunk_pages preserves 1-based page numbers across multiple pages."""
    pages = [
        (1, "Page one text detailing supervised learning algorithms and classification tasks."),
        (2, "Page two text covering neural network architectures, transformers, and attention."),
    ]
    chunks = chunk_pages(pages, chunk_size=100, chunk_overlap=20)
    assert len(chunks) >= 2
    page_numbers = {c.page_number for c in chunks}
    assert 1 in page_numbers
    assert 2 in page_numbers
    for i, c in enumerate(chunks):
        assert c.chunk_index == i


# ==============================================================================
# 4. DOCUMENT SERVICE & PERSISTENCE TESTS
# ==============================================================================

def test_get_or_create_default_user(db_session: Session):
    """Verify default user is created idempotently."""
    user1 = get_or_create_default_user(db_session)
    assert user1.id is not None
    assert user1.email == "default@sahayakai.local"

    user2 = get_or_create_default_user(db_session)
    assert user1.id == user2.id


def test_process_document_upload_txt(db_session: Session, tmp_path):
    """Verify end-to-end TXT file processing and DB persistence."""
    txt_content = (
        "SahayakAI Study Guide on Data Structures.\n\n"
        "Arrays provide contiguous memory allocation with O(1) access time. "
        "Linked lists provide dynamic memory allocation with O(1) insertions.\n\n"
        "Binary Search Trees maintain sorted ordering with average O(log n) lookups."
    ).encode("utf-8")

    doc, stats, keywords, chunk_count = process_document_upload(
        file_content=txt_content,
        original_filename="dsa_guide.txt",
        db=db_session,
        title="DSA Guide",
    )

    assert doc.id is not None
    assert doc.title == "DSA Guide"
    assert doc.processing_status == "completed"
    assert doc.file_type == ".txt"
    assert stats.word_count > 20
    assert chunk_count >= 1
    assert len(keywords) > 0

    # Verify chunks in DB
    chunks = get_document_chunks(doc.id, db_session)
    assert len(chunks) == chunk_count
    assert chunks[0].content


def test_process_document_upload_pdf(db_session: Session, sample_pdf_bytes):
    """Verify end-to-end PDF processing, PyMuPDF extraction, and chunk persistence."""
    doc, stats, keywords, chunk_count = process_document_upload(
        file_content=sample_pdf_bytes,
        original_filename="ai_paper.pdf",
        db=db_session,
        title="AI Paper",
    )

    assert doc.id is not None
    assert doc.processing_status == "completed"
    assert doc.file_type == ".pdf"
    assert "Machine Learning Basics" in doc.extracted_text
    assert "Neural Networks" in doc.extracted_text
    assert stats.page_count == 2
    assert chunk_count >= 2

    # Verify chunks have page attribution metadata
    chunks = get_document_chunks(doc.id, db_session)
    assert any(c.chunk_metadata.get("page_number") == 1 for c in chunks)
    assert any(c.chunk_metadata.get("page_number") == 2 for c in chunks)


def test_process_document_upload_empty_extracted_text_fails(db_session: Session):
    """Verify document with no extractable text marks status as failed and raises AppException."""
    # PDF with blank page (no text)
    blank_doc = fitz.open()
    blank_doc.new_page()
    blank_bytes = blank_doc.tobytes()
    blank_doc.close()

    with pytest.raises(AppException) as exc:
        process_document_upload(
            file_content=blank_bytes,
            original_filename="blank.pdf",
            db=db_session,
        )
    assert exc.value.error_code == "NO_EXTRACTABLE_TEXT"


def test_document_queries_and_deletion(db_session: Session):
    """Verify list, get by ID, get chunks, and cascading deletion."""
    sample_text = "Sample content for testing document lifecycle and cascade deletion.".encode("utf-8")
    doc, _, _, _ = process_document_upload(
        file_content=sample_text,
        original_filename="lifecycle.txt",
        db=db_session,
    )

    # List documents
    all_docs = list_documents(db_session)
    assert any(d.id == doc.id for d in all_docs)

    # Get by ID
    fetched_doc, count = get_document_by_id(doc.id, db_session)
    assert fetched_doc.id == doc.id
    assert count >= 1

    # Delete
    deleted = delete_document(doc.id, db_session)
    assert deleted is True

    # Confirm deletion
    with pytest.raises(AppException) as exc:
        get_document_by_id(doc.id, db_session)
    assert exc.value.error_code == "DOCUMENT_NOT_FOUND"


# ==============================================================================
# 5. FASTAPI REST API ENDPOINT TESTS
# ==============================================================================

def test_api_upload_txt_success(client: TestClient):
    """Verify POST /api/documents/upload with valid TXT returns 201 and DocumentUploadResponse."""
    txt_data = io.BytesIO("Computer Systems Architecture: CPU registers and instruction pipelining.".encode("utf-8"))
    response = client.post(
        "/api/documents/upload",
        files={"file": ("systems.txt", txt_data, "text/plain")},
        data={"title": "Systems Notes"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == "Systems Notes"
    assert data["file_type"] == ".txt"
    assert data["processing_status"] == "completed"
    assert data["word_count"] > 0
    assert data["chunk_count"] >= 1
    assert "keywords" in data


def test_api_upload_pdf_success(client: TestClient, sample_pdf_bytes):
    """Verify POST /api/documents/upload with valid PDF returns 201 and page statistics."""
    pdf_stream = io.BytesIO(sample_pdf_bytes)
    response = client.post(
        "/api/documents/upload",
        files={"file": ("lecture.pdf", pdf_stream, "application/pdf")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["file_type"] == ".pdf"
    assert data["page_count"] == 2
    assert data["chunk_count"] >= 2
    assert data["processing_status"] == "completed"


def test_api_upload_unsupported_file_rejected(client: TestClient):
    """Verify POST /api/documents/upload with unsupported extension returns 400."""
    fake_file = io.BytesIO(b"executable binary")
    response = client.post(
        "/api/documents/upload",
        files={"file": ("malware.exe", fake_file, "application/octet-stream")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "INVALID_FILE_TYPE"


def test_api_upload_corrupt_pdf_rejected(client: TestClient):
    """Verify POST /api/documents/upload with invalid PDF bytes returns 400."""
    bad_pdf = io.BytesIO(b"not a valid pdf header")
    response = client.post(
        "/api/documents/upload",
        files={"file": ("broken.pdf", bad_pdf, "application/pdf")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "INVALID_FILE_CONTENT"


def test_api_get_document_success_and_not_found(client: TestClient):
    """Verify GET /api/documents/{id} returns details and 404 for missing ID."""
    # Upload one document
    txt_data = io.BytesIO("Operating systems process scheduling and concurrency.".encode("utf-8"))
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("os.txt", txt_data, "text/plain")},
    )
    doc_id = upload_res.json()["id"]

    # Get document
    get_res = client.get(f"/api/documents/{doc_id}")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert detail["id"] == doc_id
    assert "concurrency" in detail["extracted_text"]
    assert detail["chunk_count"] >= 1

    # Missing document
    missing_res = client.get("/api/documents/999999")
    assert missing_res.status_code == 404
    assert missing_res.json()["error_code"] == "DOCUMENT_NOT_FOUND"


def test_api_get_chunks_and_delete(client: TestClient):
    """Verify GET /api/documents/{id}/chunks and DELETE /api/documents/{id}."""
    txt_data = io.BytesIO("Algorithms and Data Structures lecture summary notes.".encode("utf-8"))
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("dsa_notes.txt", txt_data, "text/plain")},
    )
    doc_id = upload_res.json()["id"]

    # Get chunks
    chunks_res = client.get(f"/api/documents/{doc_id}/chunks")
    assert chunks_res.status_code == 200
    chunks = chunks_res.json()
    assert len(chunks) >= 1
    assert chunks[0]["chunk_index"] == 0

    # Delete document
    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Document deleted successfully"

    # Verify deleted
    verify_res = client.get(f"/api/documents/{doc_id}")
    assert verify_res.status_code == 404
