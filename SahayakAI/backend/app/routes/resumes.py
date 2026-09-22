"""
Resume Management and Analysis API Routes.
Provides endpoints for resume upload, retrieval, deletion,
and structured ATS comparison against job descriptions.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Header, Query, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.resume import (
    JobDescriptionRequest,
    ResumeAnalysisRead,
    ResumeRead,
)
from backend.app.services.resume_service import (
    analyze_resume,
    create_resume_upload,
    delete_resume,
    get_analysis,
    get_analyses,
    get_resume,
    list_resumes,
)

router = APIRouter(prefix="/resumes", tags=["Resume Analyzer"])


@router.post(
    "",
    response_model=ResumeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a candidate resume",
    description="Accepts a PDF or TXT resume file, validates format and size, safely persists to disk, and records metadata.",
)
async def api_upload_resume(
    file: UploadFile = File(..., description="Resume file (.pdf or .txt)"),
    user_id: Optional[int] = Form(None, description="Optional user ID; defaults to default dev user"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> ResumeRead:
    resolved_user = x_user_id if x_user_id is not None else user_id
    content = await file.read()
    filename = file.filename or "uploaded_resume.txt"

    resume = create_resume_upload(
        file_content=content,
        original_filename=filename,
        db=db,
        user_id=resolved_user,
    )
    return ResumeRead.model_validate(resume)


@router.get(
    "",
    response_model=List[ResumeRead],
    summary="List candidate resumes",
    description="Lists all resumes belonging to the requesting user.",
)
def api_list_resumes(
    user_id: Optional[int] = Query(None, description="Optional user ID query param"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> List[ResumeRead]:
    resolved_user = x_user_id if x_user_id is not None else user_id
    resumes = list_resumes(db=db, user_id=resolved_user)
    return [ResumeRead.model_validate(r) for r in resumes]


@router.get(
    "/{resume_id}",
    response_model=ResumeRead,
    summary="Get resume details",
    description="Retrieves metadata for a specific resume with ownership validation.",
)
def api_get_resume(
    resume_id: int,
    user_id: Optional[int] = Query(None, description="Optional user ID query param"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> ResumeRead:
    resolved_user = x_user_id if x_user_id is not None else user_id
    resume = get_resume(db=db, resume_id=resume_id, user_id=resolved_user)
    return ResumeRead.model_validate(resume)


@router.delete(
    "/{resume_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a resume",
    description="Deletes a resume, removes its file from storage, and cascades deletion to analyses.",
)
def api_delete_resume(
    resume_id: int,
    user_id: Optional[int] = Query(None, description="Optional user ID query param"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> dict:
    resolved_user = x_user_id if x_user_id is not None else user_id
    delete_resume(db=db, resume_id=resume_id, user_id=resolved_user)
    return {"message": "Resume deleted successfully", "resume_id": resume_id}


@router.post(
    "/{resume_id}/analyze",
    response_model=ResumeAnalysisRead,
    status_code=status.HTTP_200_OK,
    summary="Analyze resume against job description",
    description="Extracts structured skills, education, and experience, compares against optional job description requirements, and calculates match score.",
)
def api_analyze_resume(
    resume_id: int,
    payload: Optional[JobDescriptionRequest] = None,
    user_id: Optional[int] = Query(None, description="Optional user ID query param"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> ResumeAnalysisRead:
    resolved_user = x_user_id if x_user_id is not None else user_id
    jd_text = payload.job_description if payload else None
    analysis = analyze_resume(
        db=db,
        resume_id=resume_id,
        job_description=jd_text,
        user_id=resolved_user,
    )
    return ResumeAnalysisRead.model_validate(analysis)


@router.get(
    "/{resume_id}/analyses",
    response_model=List[ResumeAnalysisRead],
    summary="List analyses for a resume",
    description="Retrieves historical analyses conducted on a specific resume.",
)
def api_get_analyses(
    resume_id: int,
    user_id: Optional[int] = Query(None, description="Optional user ID query param"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> List[ResumeAnalysisRead]:
    resolved_user = x_user_id if x_user_id is not None else user_id
    analyses = get_analyses(db=db, resume_id=resume_id, user_id=resolved_user)
    return [ResumeAnalysisRead.model_validate(a) for a in analyses]


@router.get(
    "/{resume_id}/analyses/{analysis_id}",
    response_model=ResumeAnalysisRead,
    summary="Get specific analysis result",
    description="Retrieves a specific resume analysis scorecard by ID.",
)
def api_get_analysis(
    resume_id: int,
    analysis_id: int,
    user_id: Optional[int] = Query(None, description="Optional user ID query param"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> ResumeAnalysisRead:
    resolved_user = x_user_id if x_user_id is not None else user_id
    analysis = get_analysis(db=db, resume_id=resume_id, analysis_id=analysis_id, user_id=resolved_user)
    return ResumeAnalysisRead.model_validate(analysis)
