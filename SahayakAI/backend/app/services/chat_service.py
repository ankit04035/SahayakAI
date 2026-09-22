"""
Study Assistant and Document-Grounded Chat Service.
Orchestrates chat session lifecycle, multi-turn history tracking,
document-grounded retrieval via existing RAG pipeline, AI provider synthesis,
and database persistence.
"""

import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.models.chat import ChatMessage, ChatSession
from backend.app.models.document import Document
from backend.app.models.user import User
from backend.app.providers import get_provider
from backend.app.rag.context_builder import build_rag_context
from backend.app.rag.models import SourceReference
from backend.app.rag.retrieval import retrieve_chunks
from backend.app.services.chat_exceptions import (
    ChatAccessDeniedError,
    ChatDocumentNotFoundError,
    ChatMessageValidationError,
    ChatSessionNotFoundError,
    DocumentOwnershipError,
)
from backend.app.services.chat_prompt import (
    build_chat_prompts,
    format_conversation_history,
)
from backend.app.services.document_service import get_or_create_default_user

logger = logging.getLogger("sahayakai.chat_service")


def create_session(
    db: Session,
    user_id: Optional[int] = None,
    title: Optional[str] = "New Chat",
    document_id: Optional[int] = None,
) -> ChatSession:
    """
    Create a new chat session.

    Args:
        db: SQLAlchemy session.
        user_id: Owner user ID; defaults to default dev user if None.
        title: Session title.
        document_id: Optional reference document to ground the conversation.

    Returns:
        Newly created and persisted ChatSession.
    """
    settings = get_settings()

    # 1. Resolve and validate user
    if user_id is None:
        user = get_or_create_default_user(db)
        resolved_user_id = user.id
    else:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = get_or_create_default_user(db)
            resolved_user_id = user.id
        else:
            resolved_user_id = user.id

    # 2. Validate optional document association and ownership
    if document_id is not None:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ChatDocumentNotFoundError(document_id=document_id)
        if doc.user_id != resolved_user_id:
            logger.warning(
                "Document ownership mismatch: document %d belongs to user %d, requested by user %d",
                document_id,
                doc.user_id,
                resolved_user_id,
            )
            raise DocumentOwnershipError(document_id=document_id)

    # 3. Sanitize title
    clean_title = (title or "New Chat").strip()
    if not clean_title:
        clean_title = "New Chat"
    clean_title = clean_title[: settings.CHAT_MAX_TITLE_CHARS]

    session = ChatSession(
        user_id=resolved_user_id,
        document_id=document_id,
        title=clean_title,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    logger.info("Created ChatSession id=%d for user_id=%d, document_id=%s", session.id, resolved_user_id, document_id)
    return session


def get_session(
    db: Session,
    session_id: int,
    user_id: Optional[int] = None,
) -> ChatSession:
    """
    Retrieve a chat session with ownership verification.

    Args:
        db: SQLAlchemy session.
        session_id: Chat session ID.
        user_id: Optional requesting user ID.

    Returns:
        ChatSession record.

    Raises:
        ChatSessionNotFoundError: If session does not exist.
        ChatAccessDeniedError: If session belongs to another user.
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise ChatSessionNotFoundError(session_id=session_id)

    if user_id is not None and session.user_id != user_id:
        logger.warning("Access denied: user %d attempted to access session %d owned by user %d", user_id, session.id, session.user_id)
        raise ChatAccessDeniedError(session_id=session_id)

    return session


def list_sessions(
    db: Session,
    user_id: Optional[int] = None,
    document_id: Optional[int] = None,
) -> List[ChatSession]:
    """
    List chat sessions belonging to a user, optionally filtered by document.
    """
    if user_id is None:
        user = get_or_create_default_user(db)
        resolved_user_id = user.id
    else:
        resolved_user_id = user_id

    query = db.query(ChatSession).filter(ChatSession.user_id == resolved_user_id)
    if document_id is not None:
        query = query.filter(ChatSession.document_id == document_id)

    return query.order_by(ChatSession.id.desc()).all()


def delete_session(
    db: Session,
    session_id: int,
    user_id: Optional[int] = None,
) -> bool:
    """
    Delete a chat session and all associated messages.
    """
    session = get_session(db=db, session_id=session_id, user_id=user_id)
    db.delete(session)
    db.commit()
    logger.info("Deleted ChatSession id=%d", session_id)
    return True


def list_messages(
    db: Session,
    session_id: int,
    user_id: Optional[int] = None,
) -> List[ChatMessage]:
    """
    List messages for a session in chronological order.
    """
    session = get_session(db=db, session_id=session_id, user_id=user_id)
    return session.messages


def send_message(
    db: Session,
    session_id: int,
    message: str,
    user_id: Optional[int] = None,
    top_k: Optional[int] = None,
    similarity_threshold: Optional[float] = None,
) -> Tuple[ChatMessage, ChatMessage, bool, bool, List[SourceReference], str, str]:
    """
    Submit a user question to a chat session, synthesize a response,
    and persist both conversational turns.

    Flow:
        1. Validate question constraints.
        2. Validate session existence and user ownership.
        3. Persist the user message turn to SQLite.
        4. Load bounded conversation history.
        5. If document-grounded session:
           a. Invoke RAG retrieval engine.
           b. If evidence is insufficient, record controlled response and skip LLM.
           c. Else, assemble context and build grounded prompt with injection defense.
        6. If general study session (no document):
           a. Build educational mentor prompt without document retrieval.
        7. Call active AI Provider (Demo, OpenAI, Gemini).
        8. Persist assistant response turn with source metadata.
        9. Return tuple of result components.

    Returns:
        Tuple of:
            (user_message, assistant_message, grounded, insufficient_evidence, sources, provider_name, model_name)
    """
    settings = get_settings()

    # 1. Validate message
    if not message or not message.strip():
        raise ChatMessageValidationError("Message cannot be empty or contain only whitespace.")

    cleaned_msg = message.strip()
    if len(cleaned_msg) > settings.CHAT_MAX_MESSAGE_CHARS:
        raise ChatMessageValidationError(
            f"Message length ({len(cleaned_msg)}) exceeds maximum limit of {settings.CHAT_MAX_MESSAGE_CHARS} characters."
        )

    # 2. Validate session and ownership
    session = get_session(db=db, session_id=session_id, user_id=user_id)

    # 3. Persist user message turn immediately
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=cleaned_msg,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 4. Load bounded conversation history (excluding the current turn just added)
    all_prior = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id, ChatMessage.id != user_msg.id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    history_window = all_prior[-settings.CHAT_HISTORY_MAX_MESSAGES :] if all_prior else []
    history_text = format_conversation_history(history_window, max_history_chars=settings.CHAT_MAX_HISTORY_CHARS)

    provider = get_provider()
    sources: List[SourceReference] = []

    # 5. Document-grounded vs General study branching
    if session.document_id is not None:
        logger.info("Executing document-grounded chat for session %d (document %d)", session.id, session.document_id)

        # Retrieve chunks using Step 7 retrieval engine
        selected_chunks, has_sufficient_evidence, scored_count = retrieve_chunks(
            document_id=session.document_id,
            query=cleaned_msg,
            db=db,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        # Handle insufficient evidence without calling LLM
        if not has_sufficient_evidence or not selected_chunks:
            logger.info("Insufficient evidence for session %d on document %d", session.id, session.document_id)
            answer_text = "The provided document does not contain sufficient relevant information to answer this question."
            grounded = False
            insufficient_evidence = True
            sources = []

            meta_record = {
                "grounded": False,
                "insufficient_evidence": True,
                "document_id": session.document_id,
                "sources": [],
            }
            assistant_msg = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=answer_text,
                source_metadata=meta_record,
            )
            db.add(assistant_msg)
            db.commit()
            db.refresh(assistant_msg)

            return user_msg, assistant_msg, grounded, insufficient_evidence, sources, provider.provider_name, provider.default_model

        # Assemble bounded context
        rag_context = build_rag_context(
            retrieved_chunks=selected_chunks,
            max_context_chars=settings.RAG_MAX_CONTEXT_CHARS,
        )
        sources = rag_context.sources

        # Build grounded prompt
        system_prompt, user_prompt = build_chat_prompts(
            user_question=cleaned_msg,
            history_text=history_text,
            context_text=rag_context.formatted_context,
            is_document_grounded=True,
        )

        # Call AI provider
        provider_resp = provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=settings.AI_TEMPERATURE,
            max_tokens=settings.AI_MAX_TOKENS,
        )
        answer_text = provider_resp.generated_text
        grounded = True
        insufficient_evidence = False

        meta_record = {
            "grounded": True,
            "insufficient_evidence": False,
            "document_id": session.document_id,
            "sources": [
                {
                    "chunk_id": s.chunk_id,
                    "chunk_index": s.chunk_index,
                    "page": s.page,
                    "similarity": round(s.similarity, 4),
                }
                for s in sources
            ],
        }
    else:
        # General study question (no document attached)
        logger.info("Executing general study chat for session %d", session.id)

        system_prompt, user_prompt = build_chat_prompts(
            user_question=cleaned_msg,
            history_text=history_text,
            is_document_grounded=False,
        )

        provider_resp = provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=settings.AI_TEMPERATURE,
            max_tokens=settings.AI_MAX_TOKENS,
        )
        answer_text = provider_resp.generated_text
        grounded = False
        insufficient_evidence = False

        meta_record = {
            "grounded": False,
            "insufficient_evidence": False,
            "document_id": None,
            "sources": [],
        }

    # 8. Persist assistant message
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=answer_text,
        source_metadata=meta_record,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return (
        user_msg,
        assistant_msg,
        grounded,
        insufficient_evidence,
        sources,
        provider_resp.provider,
        provider_resp.model,
    )
