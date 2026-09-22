"""
Comprehensive Database Model and Relationship Tests.
Verifies all 9 SQLAlchemy entities, constraints, foreign keys, cascades, timestamps, and JSON fields.
"""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine, inspect, event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models import (
    User,
    Document,
    DocumentChunk,
    ChatSession,
    ChatMessage,
    Resume,
    ResumeAnalysis,
    CareerProfile,
    Roadmap,
)


@pytest.fixture(scope="function")
def test_db():
    """Create an isolated, in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    # Enable SQLite foreign key enforcement
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    yield session, engine

    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_all_nine_tables_exist_after_initialization(test_db):
    """Test 1: Verify all 9 required tables exist in the database schema."""
    _, engine = test_db
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    expected_tables = {
        "users",
        "documents",
        "document_chunks",
        "chat_sessions",
        "chat_messages",
        "resumes",
        "resume_analyses",
        "career_profiles",
        "roadmaps",
    }
    assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"


def test_user_creation_and_fields(test_db):
    """Test 2: Verify user creation with valid attributes."""
    session, _ = test_db
    user = User(name="Ankit Sharma", email="ankit@example.com")
    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.id is not None
    assert user.name == "Ankit Sharma"
    assert user.email == "ankit@example.com"
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)
    assert user.created_at.tzinfo is not None


def test_user_email_uniqueness(test_db):
    """Test 3: Verify unique constraint on user email."""
    session, _ = test_db
    u1 = User(name="User One", email="unique@example.com")
    session.add(u1)
    session.commit()

    u2 = User(name="User Two", email="unique@example.com")
    session.add(u2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_document_user_relationship(test_db):
    """Test 4: Verify Document -> User relationship."""
    session, _ = test_db
    user = User(name="Doc Owner", email="doc_owner@example.com")
    session.add(user)
    session.commit()

    doc = Document(
        user_id=user.id,
        title="AI Career Guide",
        original_filename="guide.pdf",
        stored_filename="uuid_guide.pdf",
        file_type="pdf",
        file_size=204800,
        mime_type="application/pdf",
        extracted_text="Introduction to AI Careers...",
        processing_status="completed",
    )
    session.add(doc)
    session.commit()

    session.refresh(user)
    session.refresh(doc)
    assert len(user.documents) == 1
    assert user.documents[0].id == doc.id
    assert doc.user.id == user.id


def test_document_chunk_relationship(test_db):
    """Test 5: Verify DocumentChunk -> Document relationship."""
    session, _ = test_db
    user = User(name="Chunk Owner", email="chunk@example.com")
    session.add(user)
    session.commit()

    doc = Document(
        user_id=user.id,
        original_filename="notes.txt",
        stored_filename="uuid_notes.txt",
        file_type="txt",
        file_size=1024,
    )
    session.add(doc)
    session.commit()

    dummy_vector = [0.1] * 384
    chunk = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        content="First paragraph of notes.",
        character_count=25,
        embedding=dummy_vector,
        chunk_metadata={"page": 1},
    )
    session.add(chunk)
    session.commit()

    session.refresh(doc)
    assert len(doc.chunks) == 1
    assert doc.chunks[0].chunk_index == 0
    assert doc.chunks[0].embedding == dummy_vector
    assert doc.chunks[0].document.id == doc.id


def test_chat_session_user_relationship(test_db):
    """Test 6: Verify ChatSession -> User relationship."""
    session, _ = test_db
    user = User(name="Chat User", email="chat_user@example.com")
    session.add(user)
    session.commit()

    chat_session = ChatSession(user_id=user.id, title="Resume Advice Session")
    session.add(chat_session)
    session.commit()

    session.refresh(user)
    assert len(user.chat_sessions) == 1
    assert user.chat_sessions[0].title == "Resume Advice Session"
    assert chat_session.user.id == user.id


def test_chat_message_relationship_and_role_constraint(test_db):
    """Test 7: Verify ChatMessage -> ChatSession relationship and role check constraint."""
    session, _ = test_db
    user = User(name="Msg User", email="msg_user@example.com")
    session.add(user)
    session.commit()

    cs = ChatSession(user_id=user.id, title="QA Session")
    session.add(cs)
    session.commit()

    msg = ChatMessage(
        session_id=cs.id,
        role="user",
        content="How do I improve my resume?",
        source_metadata={"topic": "resume"},
    )
    session.add(msg)
    session.commit()

    session.refresh(cs)
    assert len(cs.messages) == 1
    assert cs.messages[0].content == "How do I improve my resume?"
    assert cs.messages[0].session.id == cs.id

    # Test invalid role constraint
    bad_msg = ChatMessage(session_id=cs.id, role="hacker", content="Invalid role message")
    session.add(bad_msg)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_resume_user_relationship(test_db):
    """Test 8: Verify Resume -> User relationship."""
    session, _ = test_db
    user = User(name="Applicant", email="applicant@example.com")
    session.add(user)
    session.commit()

    resume = Resume(
        user_id=user.id,
        original_filename="john_doe_resume.pdf",
        stored_filename="uuid_john_doe.pdf",
        file_type="pdf",
        file_size=512000,
        processing_status="uploaded",
    )
    session.add(resume)
    session.commit()

    session.refresh(user)
    assert len(user.resumes) == 1
    assert user.resumes[0].original_filename == "john_doe_resume.pdf"
    assert resume.user.id == user.id


def test_resume_analysis_relationship(test_db):
    """Test 9: Verify ResumeAnalysis -> Resume 1:1 relationship and structured fields."""
    session, _ = test_db
    user = User(name="Candidate", email="candidate@example.com")
    session.add(user)
    session.commit()

    resume = Resume(
        user_id=user.id,
        original_filename="cv.pdf",
        stored_filename="uuid_cv.pdf",
        file_type="pdf",
        file_size=102400,
    )
    session.add(resume)
    session.commit()

    analysis = ResumeAnalysis(
        resume_id=resume.id,
        job_description="Backend Python Engineer with FastAPI experience",
        extracted_skills=["Python", "FastAPI", "Docker"],
        matched_skills=["Python", "FastAPI"],
        missing_skills=["Docker"],
        match_score=85.5,
        recommendations=["Add containerization project to your portfolio"],
    )
    session.add(analysis)
    session.commit()

    session.refresh(resume)
    assert resume.analysis is not None
    assert resume.analysis.match_score == 85.5
    assert resume.analysis.extracted_skills == ["Python", "FastAPI", "Docker"]
    assert resume.analysis.resume.id == resume.id


def test_career_profile_user_relationship(test_db):
    """Test 10: Verify CareerProfile -> User relationship."""
    session, _ = test_db
    user = User(name="Career Seeker", email="seeker@example.com")
    session.add(user)
    session.commit()

    profile = CareerProfile(
        user_id=user.id,
        degree="B.Tech in Computer Science",
        current_skills=["Python", "Data Structures"],
        experience="Fresher with 2 internship projects",
        interests=["Machine Learning", "System Design"],
        target_role="Machine Learning Engineer",
    )
    session.add(profile)
    session.commit()

    session.refresh(user)
    assert len(user.career_profiles) == 1
    assert user.career_profiles[0].target_role == "Machine Learning Engineer"
    assert profile.user.id == user.id


def test_roadmap_career_profile_relationship(test_db):
    """Test 11: Verify Roadmap -> CareerProfile relationship."""
    session, _ = test_db
    user = User(name="Learner", email="learner@example.com")
    session.add(user)
    session.commit()

    profile = CareerProfile(user_id=user.id, target_role="Data Scientist")
    session.add(profile)
    session.commit()

    roadmap = Roadmap(
        career_profile_id=profile.id,
        title="6-Month Data Scientist Roadmap",
        recommended_skills=["Pandas", "Scikit-Learn", "PyTorch"],
        missing_skills=["PyTorch", "Deep Learning"],
        learning_order=["Phase 1: Statistics", "Phase 2: ML", "Phase 3: Deep Learning"],
        weekly_plan=[{"week": 1, "topic": "Probability and Linear Algebra"}],
        interview_topics=["Overfitting vs Underfitting", "Bias-Variance Tradeoff"],
        recommendation_reasons=["Industry benchmark requires deep learning skills"],
    )
    session.add(roadmap)
    session.commit()

    session.refresh(profile)
    assert len(profile.roadmaps) == 1
    assert profile.roadmaps[0].title == "6-Month Data Scientist Roadmap"
    assert roadmap.career_profile.id == profile.id


def test_cascade_delete_behavior(test_db):
    """Test 12: Verify cascading deletion of child entities when User is deleted."""
    session, _ = test_db
    user = User(name="Cascade User", email="cascade@example.com")
    session.add(user)
    session.commit()

    # Add document with chunk
    doc = Document(
        user_id=user.id,
        original_filename="doc.pdf",
        stored_filename="uuid_doc.pdf",
        file_type="pdf",
        file_size=1000,
    )
    session.add(doc)
    session.commit()
    chunk = DocumentChunk(document_id=doc.id, chunk_index=0, content="test chunk", character_count=10)
    session.add(chunk)

    # Add chat session with message
    cs = ChatSession(user_id=user.id, title="Chat to delete")
    session.add(cs)
    session.commit()
    msg = ChatMessage(session_id=cs.id, role="user", content="Hello")
    session.add(msg)

    # Add resume with analysis
    resume = Resume(
        user_id=user.id,
        original_filename="res.pdf",
        stored_filename="uuid_res.pdf",
        file_type="pdf",
        file_size=2000,
    )
    session.add(resume)
    session.commit()
    analysis = ResumeAnalysis(resume_id=resume.id, match_score=90.0)
    session.add(analysis)

    # Add career profile with roadmap
    cp = CareerProfile(user_id=user.id, target_role="DevOps")
    session.add(cp)
    session.commit()
    rm = Roadmap(career_profile_id=cp.id, title="DevOps Roadmap")
    session.add(rm)
    session.commit()

    # Pre-capture IDs before cascading deletion to avoid accessing deleted instances
    doc_id = doc.id
    chunk_id = chunk.id
    cs_id = cs.id
    msg_id = msg.id
    resume_id = resume.id
    analysis_id = analysis.id
    cp_id = cp.id
    rm_id = rm.id

    # Now delete the parent user
    session.delete(user)
    session.commit()

    # Assert all child records have been cascaded and deleted
    assert session.query(Document).filter_by(id=doc_id).first() is None
    assert session.query(DocumentChunk).filter_by(id=chunk_id).first() is None
    assert session.query(ChatSession).filter_by(id=cs_id).first() is None
    assert session.query(ChatMessage).filter_by(id=msg_id).first() is None
    assert session.query(Resume).filter_by(id=resume_id).first() is None
    assert session.query(ResumeAnalysis).filter_by(id=analysis_id).first() is None
    assert session.query(CareerProfile).filter_by(id=cp_id).first() is None
    assert session.query(Roadmap).filter_by(id=rm_id).first() is None


def test_required_fields_reject_null(test_db):
    """Test 13: Verify non-nullable column constraints reject missing required values."""
    session, _ = test_db
    # User without email
    bad_user = User(name="No Email")
    session.add(bad_user)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    # User without name
    bad_user2 = User(email="noname@example.com")
    session.add(bad_user2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_timestamps_creation_and_timezone(test_db):
    """Test 14: Verify timestamps are populated with timezone-aware UTC dates."""
    session, _ = test_db
    user = User(name="Timestamp User", email="time@example.com")
    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.created_at is not None
    assert user.updated_at is not None
    assert user.created_at.tzinfo == timezone.utc
    assert user.updated_at.tzinfo == timezone.utc


def test_database_session_safe_closure(test_db):
    """Test 15: Verify database session can execute queries and close safely."""
    session, _ = test_db
    assert session.is_active
    session.execute(User.__table__.select())
    session.close()
    assert not session.in_transaction()
    assert len(session.identity_map) == 0


def test_json_fields_serialization_and_deserialization(test_db):
    """Test 16: Verify JSON-compatible structured fields preserve types across roundtrips."""
    session, _ = test_db
    user = User(name="JSON Tester", email="json@example.com")
    session.add(user)
    session.commit()

    complex_skills = {
        "languages": ["Python", "Go", "TypeScript"],
        "frameworks": ["FastAPI", "React", "PyTorch"],
        "metrics": {"years": 3, "score": 9.5},
    }
    profile = CareerProfile(
        user_id=user.id,
        current_skills=complex_skills,
        interests=["RAG", "Distributed Systems"],
        target_role="Staff AI Engineer",
    )
    session.add(profile)
    session.commit()

    session.refresh(profile)
    assert profile.current_skills == complex_skills
    assert profile.current_skills["languages"] == ["Python", "Go", "TypeScript"]
    assert profile.interests == ["RAG", "Distributed Systems"]
