"""
Chat and Study Assistant API Routes.
Provides REST endpoints for chat session creation, listing, deletion,
message dispatch, and message history inspection.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.chat import (
    ChatMessageRead,
    ChatRequest,
    ChatResponse,
    ChatSessionCreate,
    ChatSessionRead,
    ChatSessionUpdate,
)
from backend.app.schemas.rag import SourceReferenceSchema
from backend.app.services.chat_service import (
    create_session,
    delete_session,
    get_session,
    list_messages,
    list_sessions,
    send_message,
)

router = APIRouter(prefix="/chat", tags=["Chat & Study Assistant"])


@router.post(
    "/sessions",
    response_model=ChatSessionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a chat session",
    description="Creates a new conversational chat session, optionally grounded in an uploaded reference document.",
)
def api_create_session(
    payload: ChatSessionCreate,
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional requesting user ID header"),
    db: Session = Depends(get_db),
) -> ChatSessionRead:
    user_id = x_user_id if x_user_id is not None else payload.user_id
    session = create_session(
        db=db,
        user_id=user_id,
        title=payload.title,
        document_id=payload.document_id,
    )
    return ChatSessionRead.model_validate(session)


@router.get(
    "/sessions",
    response_model=List[ChatSessionRead],
    summary="List chat sessions",
    description="Retrieves all chat sessions belonging to the requesting user.",
)
def api_list_sessions(
    document_id: Optional[int] = Query(None, description="Filter sessions by associated document ID"),
    user_id: Optional[int] = Query(None, description="Optional user ID query parameter"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional requesting user ID header"),
    db: Session = Depends(get_db),
) -> List[ChatSessionRead]:
    resolved_user = x_user_id if x_user_id is not None else user_id
    sessions = list_sessions(db=db, user_id=resolved_user, document_id=document_id)
    return [ChatSessionRead.model_validate(s) for s in sessions]


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionRead,
    summary="Get chat session details",
    description="Retrieves metadata for a specific chat session with user ownership verification.",
)
def api_get_session(
    session_id: int,
    user_id: Optional[int] = Query(None, description="Optional user ID query parameter"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional requesting user ID header"),
    db: Session = Depends(get_db),
) -> ChatSessionRead:
    resolved_user = x_user_id if x_user_id is not None else user_id
    session = get_session(db=db, session_id=session_id, user_id=resolved_user)
    return ChatSessionRead.model_validate(session)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a chat session",
    description="Deletes a chat session and cascades deletion to all contained conversational messages.",
)
def api_delete_session(
    session_id: int,
    user_id: Optional[int] = Query(None, description="Optional user ID query parameter"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional requesting user ID header"),
    db: Session = Depends(get_db),
) -> dict:
    resolved_user = x_user_id if x_user_id is not None else user_id
    delete_session(db=db, session_id=session_id, user_id=resolved_user)
    return {"message": "Chat session deleted successfully", "session_id": session_id}


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message to a chat session",
    description="Submits a question to the study assistant. If the session is associated with a document, answers are grounded via vector retrieval. Returns the persisted user and assistant messages.",
)
def api_send_message(
    session_id: int,
    payload: ChatRequest,
    user_id: Optional[int] = Query(None, description="Optional user ID query parameter"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional requesting user ID header"),
    db: Session = Depends(get_db),
) -> ChatResponse:
    resolved_user = x_user_id if x_user_id is not None else user_id
    user_msg, assistant_msg, grounded, insufficient_evidence, sources, provider, model = send_message(
        db=db,
        session_id=session_id,
        message=payload.message,
        user_id=resolved_user,
        top_k=payload.top_k,
        similarity_threshold=payload.similarity_threshold,
    )

    source_schemas = [
        SourceReferenceSchema(
            chunk_id=s.chunk_id,
            chunk_index=s.chunk_index,
            page=s.page,
            similarity=s.similarity,
        )
        for s in sources
    ]

    return ChatResponse(
        session_id=session_id,
        user_message=ChatMessageRead.model_validate(user_msg),
        assistant_message=ChatMessageRead.model_validate(assistant_msg),
        grounded=grounded,
        insufficient_evidence=insufficient_evidence,
        sources=source_schemas,
        provider=provider,
        model=model,
    )


@router.get(
    "/sessions/{session_id}/messages",
    response_model=List[ChatMessageRead],
    summary="List messages in a chat session",
    description="Retrieves the chronologically ordered message history for a specific chat session.",
)
def api_list_messages(
    session_id: int,
    user_id: Optional[int] = Query(None, description="Optional user ID query parameter"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional requesting user ID header"),
    db: Session = Depends(get_db),
) -> List[ChatMessageRead]:
    resolved_user = x_user_id if x_user_id is not None else user_id
    messages = list_messages(db=db, session_id=session_id, user_id=resolved_user)
    return [ChatMessageRead.model_validate(m) for m in messages]
