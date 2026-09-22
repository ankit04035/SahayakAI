"""
Career Profile and Career Roadmap API Routes.
Provides endpoints for career profile management, deterministic skill gap analysis,
and milestone-based roadmap generation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.career import (
    CareerProfileCreate,
    CareerProfileRead,
    CareerProfileUpdate,
    RoadmapGenerateRequest,
    RoadmapRead,
)
from backend.app.services.career_service import (
    delete_career_profile,
    delete_roadmap,
    generate_roadmap,
    get_career_profile,
    get_roadmap,
    list_roadmaps,
    update_career_profile,
    upsert_career_profile,
)

router = APIRouter(prefix="/career", tags=["Career Roadmap"])


# ==============================================================================
# CAREER PROFILE ENDPOINTS
# ==============================================================================

@router.post(
    "/profile",
    response_model=CareerProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update user career profile",
    description="Creates or idempotently updates the career profile for the requesting user.",
)
def api_upsert_career_profile(
    profile_in: CareerProfileCreate,
    user_id: Optional[int] = Query(None, description="Optional user ID query param"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> CareerProfileRead:
    resolved_user = x_user_id if x_user_id is not None else user_id
    profile = upsert_career_profile(db=db, profile_in=profile_in, user_id=resolved_user)
    return CareerProfileRead.model_validate(profile)


@router.get(
    "/profile",
    response_model=CareerProfileRead,
    summary="Get user career profile",
    description="Retrieves the career profile of the requesting user.",
)
def api_get_career_profile(
    user_id: Optional[int] = Query(None, description="Optional user ID query param"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> CareerProfileRead:
    resolved_user = x_user_id if x_user_id is not None else user_id
    profile = get_career_profile(db=db, user_id=resolved_user)
    return CareerProfileRead.model_validate(profile)


@router.put(
    "/profile",
    response_model=CareerProfileRead,
    summary="Update user career profile",
    description="Updates specific fields of the career profile for the requesting user.",
)
def api_update_career_profile(
    profile_in: CareerProfileUpdate,
    user_id: Optional[int] = Query(None, description="Optional user ID query param"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> CareerProfileRead:
    resolved_user = x_user_id if x_user_id is not None else user_id
    profile = update_career_profile(db=db, profile_in=profile_in, user_id=resolved_user)
    return CareerProfileRead.model_validate(profile)


@router.delete(
    "/profile",
    status_code=status.HTTP_200_OK,
    summary="Delete user career profile",
    description="Deletes the user's career profile and cascades deletion to all associated roadmaps.",
)
def api_delete_career_profile(
    user_id: Optional[int] = Query(None, description="Optional user ID query param"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> dict:
    resolved_user = x_user_id if x_user_id is not None else user_id
    delete_career_profile(db=db, user_id=resolved_user)
    return {"message": "Career profile deleted successfully"}


# ==============================================================================
# CAREER ROADMAP ENDPOINTS
# ==============================================================================

@router.post(
    "/roadmaps/generate",
    response_model=RoadmapRead,
    status_code=status.HTTP_201_CREATED,
    summary="Generate personalized career roadmap",
    description="Analyzes career profile, computes skill gaps against target role, and generates structured roadmap.",
)
def api_generate_roadmap(
    request: Optional[RoadmapGenerateRequest] = None,
    user_id: Optional[int] = Query(None, description="Optional user ID query param"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> RoadmapRead:
    resolved_user = x_user_id if x_user_id is not None else user_id
    roadmap = generate_roadmap(db=db, request=request, user_id=resolved_user)
    return RoadmapRead.model_validate(roadmap)


@router.get(
    "/roadmaps",
    response_model=List[RoadmapRead],
    summary="List user career roadmaps",
    description="Lists all roadmaps generated for the requesting user's profile.",
)
def api_list_roadmaps(
    user_id: Optional[int] = Query(None, description="Optional user ID query param"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> List[RoadmapRead]:
    resolved_user = x_user_id if x_user_id is not None else user_id
    roadmaps = list_roadmaps(db=db, user_id=resolved_user)
    return [RoadmapRead.model_validate(r) for r in roadmaps]


@router.get(
    "/roadmaps/{roadmap_id}",
    response_model=RoadmapRead,
    summary="Get specific roadmap",
    description="Retrieves a specific career roadmap by ID with ownership enforcement.",
)
def api_get_roadmap(
    roadmap_id: int,
    user_id: Optional[int] = Query(None, description="Optional user ID query param"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> RoadmapRead:
    resolved_user = x_user_id if x_user_id is not None else user_id
    roadmap = get_roadmap(db=db, roadmap_id=roadmap_id, user_id=resolved_user)
    return RoadmapRead.model_validate(roadmap)


@router.delete(
    "/roadmaps/{roadmap_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete specific roadmap",
    description="Deletes a specific career roadmap with ownership enforcement.",
)
def api_delete_roadmap(
    roadmap_id: int,
    user_id: Optional[int] = Query(None, description="Optional user ID query param"),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="Optional user ID header"),
    db: Session = Depends(get_db),
) -> dict:
    resolved_user = x_user_id if x_user_id is not None else user_id
    delete_roadmap(db=db, roadmap_id=roadmap_id, user_id=resolved_user)
    return {"message": "Roadmap deleted successfully", "roadmap_id": roadmap_id}
