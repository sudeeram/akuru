import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.weaknesses import RecommendationListResponse, RecommendationResponse, RecommendationReview
from app.security import Principal
from app.services import weaknesses

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("", response_model=RecommendationListResponse)
def recommendations(principal: Annotated[Principal, Depends(require_roles("student", "parent", "admin"))],
                    db: Annotated[Session, Depends(get_db)],
                    student_id: Annotated[uuid.UUID | None, Query(alias="studentId")] = None):
    return weaknesses.list_recommendations(db, principal, student_id)

@router.post("/{recommendation_id}/review", response_model=RecommendationResponse)
def review_recommendation(recommendation_id: uuid.UUID, payload: RecommendationReview,
                          principal: Annotated[Principal, Depends(require_csrf_roles("parent", "admin"))],
                          db: Annotated[Session, Depends(get_db)]):
    return weaknesses.review(db, principal, recommendation_id, payload)
