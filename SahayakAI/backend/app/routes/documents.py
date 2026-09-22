"""
Document Management and Processing API Routes.
Provides endpoints for document upload, retrieval, chunk listing, and deletion.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Header, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.nlp.keyword_extractor import extract_keywords
from backend.app.nlp.text_statistics import compute_text_statistics
from backend.app.schemas.document import (
    DocumentChunkRead,
    DocumentDetailRead,
    DocumentRead,
    DocumentUploadResponse,
)
from backend.app.schemas.rag import (
    EmbedChunksResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    SourceReferenceSchema,
)
from backend.app.rag.embedding_service import embed_document_chunks
from backend.app.rag.rag_service import query_document
from backend.app.services.document_service import (
    delete_document,
    get_document_by_id,
    get_document_chunks,
    list_documents,
    process_document_upload,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process a reference document",
    description="Accepts a PDF or TXT file, validates format/size, extracts text, cleans text, computes statistics and keywords, chunks the content, and persists metadata in the database.",
)
async def upload_document(
    file: UploadFile = File(..., description="Document file (.pdf or .txt)"),
    title: Optional[str] = Form(None, description="Optional custom title for the document"),
    user_id: Optional[int] = Form(None, description="Optional user ID; defaults to default dev user"),
    auto_embed: bool = Form(True, description="Whether to automatically compute embeddings upon upload"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> DocumentUploadResponse:
    resolved_user = x_user_id if x_user_id is not None else user_id
    content = await file.read()
    filename = file.filename or "uploaded_document.txt"

    doc, stats, keywords, chunk_count = process_document_upload(
        file_content=content,
        original_filename=filename,
        db=db,
        user_id=resolved_user,
        title=title,
    )

    # Automatically compute embeddings if requested and chunks exist
    if auto_embed and chunk_count > 0:
        try:
            embed_document_chunks(document_id=doc.id, db=db)
        except Exception:
            pass

    return DocumentUploadResponse(
        id=doc.id,
        user_id=doc.user_id,
        title=doc.title,
        original_filename=doc.original_filename,
        stored_filename=doc.stored_filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        processing_status=doc.processing_status,
        character_count=stats.character_count,
        word_count=stats.word_count,
        page_count=stats.page_count,
        chunk_count=chunk_count,
        primary_language=stats.primary_language,
        keywords=keywords,
        created_at=doc.created_at,
    )


@router.get(
    "",
    response_model=List[DocumentRead],
    summary="List uploaded documents",
    description="Retrieve a paginated list of uploaded documents ordered by creation date descending.",
)
def get_documents(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum records to return"),
    db: Session = Depends(get_db),
) -> List[DocumentRead]:
    resolved_user = x_user_id if x_user_id is not None else user_id
    return list_documents(db=db, user_id=resolved_user, skip=skip, limit=limit)


@router.get(
    "/{document_id}",
    response_model=DocumentDetailRead,
    summary="Get document details by ID",
    description="Retrieve document metadata, processing status, statistics, and keyword summaries.",
)
def get_document(
    document_id: int,
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> DocumentDetailRead:
    doc, chunk_count = get_document_by_id(document_id=document_id, db=db, user_id=x_user_id)
    stats = compute_text_statistics(doc.extracted_text or "")
    keywords = extract_keywords(doc.extracted_text or "", top_n=10)

    return DocumentDetailRead(
        id=doc.id,
        user_id=doc.user_id,
        title=doc.title,
        original_filename=doc.original_filename,
        stored_filename=doc.stored_filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        extracted_text=doc.extracted_text,
        processing_status=doc.processing_status,
        chunk_count=chunk_count,
        character_count=stats.character_count,
        word_count=stats.word_count,
        page_count=stats.page_count,
        primary_language=stats.primary_language,
        keywords=keywords,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get(
    "/{document_id}/chunks",
    response_model=List[DocumentChunkRead],
    summary="Get document chunks",
    description="Retrieve paginated text chunks for a document ordered by chunk_index.",
)
def get_chunks(
    document_id: int,
    skip: int = Query(0, ge=0, description="Offset for chunks"),
    limit: int = Query(50, ge=1, le=200, description="Limit for chunks"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> List[DocumentChunkRead]:
    return get_document_chunks(document_id=document_id, db=db, skip=skip, limit=limit, user_id=x_user_id)


@router.delete(
    "/{document_id}",
    summary="Delete a document",
    description="Delete a document and all associated chunks from database and disk storage.",
)
def remove_document(
    document_id: int,
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> dict:
    delete_document(document_id=document_id, db=db, user_id=x_user_id)
    return {"message": "Document deleted successfully", "id": document_id}


@router.post(
    "/{document_id}/embed",
    response_model=EmbedChunksResponse,
    summary="Compute and persist embeddings for document chunks",
    description="Generates 384-dimensional SentenceTransformer embeddings for all chunks of the specified document.",
)
def embed_chunks(
    document_id: int,
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> EmbedChunksResponse:
    # Verify ownership before embedding
    get_document_by_id(document_id=document_id, db=db, user_id=x_user_id)
    count = embed_document_chunks(document_id=document_id, db=db)
    return EmbedChunksResponse(
        document_id=document_id,
        embedded_chunks=count,
        status="completed",
    )


@router.post(
    "/{document_id}/ask",
    response_model=RAGQueryResponse,
    summary="Ask a question grounded in an uploaded document",
    description="Performs semantic vector retrieval against document chunks and generates an evidence-grounded answer using the configured AI provider.",
)
def ask_document_question(
    document_id: int,
    request: RAGQueryRequest,
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> RAGQueryResponse:
    # Verify ownership before query
    get_document_by_id(document_id=document_id, db=db, user_id=x_user_id)
    result = query_document(
        document_id=document_id,
        question=request.question,
        db=db,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
    )
    return RAGQueryResponse(
        answer=result.answer,
        grounded=result.grounded,
        provider=result.provider,
        model=result.model,
        sources=[
            SourceReferenceSchema(
                chunk_id=s.chunk_id,
                chunk_index=s.chunk_index,
                page=s.page,
                similarity=s.similarity,
            )
            for s in result.sources
        ],
        query=result.query,
        retrieved_count=result.retrieved_count,
        insufficient_evidence=result.insufficient_evidence,
    )
