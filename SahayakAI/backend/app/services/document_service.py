"""
Document Processing and Management Service.
Handles document upload, validation, disk persistence, text extraction (PDF/TXT),
cleaning, statistics generation, keyword extraction, boundary-aware chunking,
and transactional database persistence.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import fitz  # PyMuPDF
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.exceptions import AppException
from backend.app.models.document import Document, DocumentChunk
from backend.app.models.user import User
from backend.app.nlp.chunker import chunk_pages, chunk_text
from backend.app.nlp.keyword_extractor import extract_keywords
from backend.app.nlp.text_cleaner import clean_text
from backend.app.nlp.text_statistics import (
    DocumentStatistics,
    compute_text_statistics,
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

logger = logging.getLogger("sahayakai.document_service")


def get_or_create_default_user(db: Session) -> User:
    """
    Ensure a baseline default development user exists for pre-authentication operations.
    Idempotent and deterministic.
    """
    default_email = "default@sahayakai.local"
    user = db.query(User).filter(User.email == default_email).first()
    if not user:
        user = User(
            email=default_email,
            name="Default SahayakAI User",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def process_document_upload(
    file_content: bytes,
    original_filename: str,
    db: Session,
    user_id: Optional[int] = None,
    title: Optional[str] = None,
) -> Tuple[Document, DocumentStatistics, List[Dict[str, Any]], int]:
    """
    Execute end-to-end document processing pipeline:
    1. Validation (extension, size, magic bytes, decodability)
    2. File storage (safe directory path, traversal prevention)
    3. DB initialization (Document status: processing)
    4. Text extraction (PyMuPDF for PDF, multi-encoding decode for TXT)
    5. Text cleaning (Unicode NFC, whitespace normalization, PDF hyphenation)
    6. Document statistics & language detection
    7. Deterministic keyword extraction
    8. Boundary-aware chunking with page attribution
    9. Transactional DB persistence of Document and DocumentChunks
    """
    settings = get_settings()

    # 1. Validation
    ext = validate_file_metadata(original_filename, len(file_content))
    mime_type, enc_or_type = validate_file_content(file_content, ext)

    # 2. Resolve User
    if user_id is None:
        user = get_or_create_default_user(db)
        resolved_user_id = user.id
    else:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AppException(
                message=f"User with ID {user_id} not found.",
                status_code=404,
                error_code="USER_NOT_FOUND",
            )
        resolved_user_id = user_id

    # 3. Safe Storage
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_original_name = sanitize_filename(original_filename)
    stored_filename = generate_stored_filename(original_filename)
    storage_path = get_safe_storage_path(upload_dir, stored_filename)

    try:
        with open(storage_path, "wb") as f:
            f.write(file_content)
    except Exception as err:
        logger.error("Failed to write document to storage: %s", err, exc_info=True)
        raise AppException(
            message=f"Failed to persist file to disk: {str(err)}",
            status_code=500,
            error_code="STORAGE_WRITE_ERROR",
        )

    # 4. DB Record: processing
    doc_title = title.strip() if title and title.strip() else safe_original_name
    doc_record = Document(
        user_id=resolved_user_id,
        title=doc_title,
        original_filename=safe_original_name,
        stored_filename=stored_filename,
        file_type=ext,
        file_size=len(file_content),
        mime_type=mime_type,
        processing_status="processing",
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    # 5. Extraction, Cleaning, Stats, Keywords, Chunking
    try:
        pages: List[Tuple[int, str]] = []

        if ext == ".pdf":
            try:
                with fitz.open(stream=file_content, filetype="pdf") as pdf_doc:
                    page_count = len(pdf_doc)
                    if page_count == 0:
                        raise AppException(
                            message="Uploaded PDF contains no pages.",
                            status_code=400,
                            error_code="INVALID_FILE_CONTENT",
                        )
                    for idx in range(page_count):
                        raw_page = pdf_doc[idx].get_text()
                        cleaned_page = clean_text(raw_page)
                        pages.append((idx + 1, cleaned_page))
            except Exception as pdf_err:
                if isinstance(pdf_err, AppException):
                    raise pdf_err
                raise AppException(
                    message=f"Failed to extract text from PDF document: {str(pdf_err)}",
                    status_code=400,
                    error_code="PDF_EXTRACTION_ERROR",
                )
            combined_text = "\n\n".join([p[1] for p in pages if p[1].strip()]).strip()

        elif ext == ".txt":
            raw_text = file_content.decode(enc_or_type, errors="replace")
            combined_text = clean_text(raw_text)
            page_count = 1
            pages = [(1, combined_text)]
        else:
            raise AppException(
                message=f"Unsupported file type '{ext}'",
                status_code=400,
                error_code="INVALID_FILE_TYPE",
            )

        if not combined_text or not combined_text.strip():
            raise AppException(
                message="No extractable text found in uploaded document.",
                status_code=400,
                error_code="NO_EXTRACTABLE_TEXT",
            )

        # 6. Document Statistics & Language
        stats = compute_text_statistics(combined_text, page_count=page_count)

        # 7. Keywords
        keywords = extract_keywords(combined_text, top_n=15)

        # 8. Boundary-Aware Chunking
        chunk_items = chunk_pages(
            pages,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        if not chunk_items:
            chunk_items = chunk_text(
                combined_text,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
                page_number=1,
            )

        # 9. Persist Chunks and finalize Document record
        for item in chunk_items:
            chunk_entity = DocumentChunk(
                document_id=doc_record.id,
                chunk_index=item.chunk_index,
                content=item.content,
                character_count=item.character_count,
                chunk_metadata=item.chunk_metadata,
            )
            db.add(chunk_entity)

        doc_record.extracted_text = combined_text
        doc_record.processing_status = "completed"
        db.commit()
        db.refresh(doc_record)

        return doc_record, stats, keywords, len(chunk_items)

    except Exception as exc:
        db.rollback()
        try:
            doc_record.processing_status = "failed"
            db.commit()
        except Exception:
            pass

        logger.error("Document processing failed for %s: %s", original_filename, exc, exc_info=True)
        if isinstance(exc, AppException):
            raise exc
        raise AppException(
            message=f"Failed to process document: {str(exc)}",
            status_code=500,
            error_code="DOCUMENT_PROCESSING_FAILED",
        )


def get_document_by_id(document_id: int, db: Session) -> Tuple[Document, int]:
    """
    Retrieve document by ID and count its associated chunks.
    Raises 404 if not found.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise AppException(
            message=f"Document with ID {document_id} not found.",
            status_code=404,
            error_code="DOCUMENT_NOT_FOUND",
        )
    chunk_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).count()
    return doc, chunk_count


def get_document_chunks(
    document_id: int,
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> List[DocumentChunk]:
    """
    Retrieve paginated chunks for a given document ordered by chunk_index.
    """
    _ = get_document_by_id(document_id, db)
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return chunks


def list_documents(
    db: Session,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Document]:
    """
    List documents ordered by most recent first.
    """
    query = db.query(Document)
    if user_id is not None:
        query = query.filter(Document.user_id == user_id)
    return query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()


def delete_document(document_id: int, db: Session) -> bool:
    """
    Delete a document from database (cascading chunks) and remove stored disk file.
    """
    doc, _ = get_document_by_id(document_id, db)
    settings = get_settings()

    try:
        storage_path = get_safe_storage_path(settings.UPLOAD_DIR, doc.stored_filename)
        if storage_path.exists():
            storage_path.unlink()
    except Exception as err:
        logger.warning("Could not delete stored file %s: %s", doc.stored_filename, err)

    db.delete(doc)
    db.commit()
    return True
