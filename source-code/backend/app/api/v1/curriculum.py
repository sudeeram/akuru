from typing import Annotated

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.curriculum import CatalogResponse
from app.schemas.curriculum_plans import (
    CoverageDiagnosticResponse, CurriculumPlanResponse, PublishPlanRequest,
    QuestionPoolDiagnosticResponse, SavePlanRequest,
)
from app.permissions import require_csrf_roles, require_roles
from app.security import Principal, get_principal
from app.services.curriculum import get_catalog
from app.services.curriculum_plans import (
    create_next_draft, get_plan, publish_plan, question_pool_diagnostic, save_plan, student_coverage,
)


router = APIRouter(tags=["curriculum"])


@router.get("/catalog", response_model=CatalogResponse)
def catalog(
    _principal: Annotated[Principal, Depends(get_principal)],
    db: Annotated[Session, Depends(get_db)],
) -> CatalogResponse:
    return get_catalog(db)


@router.get("/admin/curriculum-plans/{subject_id}", response_model=CurriculumPlanResponse)
def read_curriculum_plan(subject_id: str, _principal: Annotated[Principal, Depends(require_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return get_plan(db, subject_id)


@router.post("/admin/curriculum-plans/{subject_id}", response_model=CurriculumPlanResponse)
def write_curriculum_plan(subject_id: str, payload: SavePlanRequest, principal: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return save_plan(db, principal, subject_id, payload)


@router.post("/admin/curriculum-plans/{subject_id}/draft", response_model=CurriculumPlanResponse)
def start_curriculum_plan_draft(subject_id: str, principal: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return create_next_draft(db, principal, subject_id)


@router.post("/admin/curriculum-plans/{subject_id}/publish", response_model=CurriculumPlanResponse)
def publish_curriculum_plan(subject_id: str, payload: PublishPlanRequest, principal: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return publish_plan(db, principal, subject_id, payload)


@router.get("/admin/students/{student_id}/coverage", response_model=CoverageDiagnosticResponse)
def read_student_coverage(student_id: uuid.UUID, subjectId: str, _principal: Annotated[Principal, Depends(require_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return student_coverage(db, student_id, subjectId)


@router.get("/admin/students/{student_id}/question-pool", response_model=QuestionPoolDiagnosticResponse)
def read_question_pool(
    student_id: uuid.UUID, subjectId: str,
    _principal: Annotated[Principal, Depends(require_roles("admin"))],
    db: Annotated[Session, Depends(get_db)],
    questionCount: Annotated[int, Query(ge=0, le=500)] = 0,
    marks: Annotated[int, Query(ge=0, le=10000)] = 0,
):
    return question_pool_diagnostic(db, student_id, subjectId, questionCount, marks)
