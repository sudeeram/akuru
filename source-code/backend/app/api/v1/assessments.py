import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.assessments import (AnswerSave, AssessmentListResponse, AssessmentResponse, AssessmentStart,
    BlueprintCreate, BlueprintResponse, SubmissionRequest)
from app.security import Principal
from app.services import assessments
from app.services import documents
from app.storage import ObjectStorage, get_storage

router = APIRouter(prefix="/assessments", tags=["assessments"])

@router.get("", response_model=AssessmentListResponse)
def list_rows(principal: Annotated[Principal, Depends(require_roles("student"))], db: Annotated[Session, Depends(get_db)]):
    return assessments.list_assessments(db, principal)

@router.get("/blueprints", response_model=list[BlueprintResponse])
def blueprints(principal: Annotated[Principal, Depends(require_roles("admin", "student"))], db: Annotated[Session, Depends(get_db)]):
    return assessments.list_blueprints(db, principal)

@router.post("/admin/blueprints", response_model=BlueprintResponse, status_code=201)
def create_blueprint(payload: BlueprintCreate, principal: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return assessments.create_blueprint(db, principal, payload)

@router.post("/start", response_model=AssessmentResponse, status_code=201)
def start(payload: AssessmentStart, principal: Annotated[Principal, Depends(require_csrf_roles("student"))], db: Annotated[Session, Depends(get_db)]):
    return assessments.start(db, principal, payload)

@router.post("/{assessment_id}/answers", response_model=AssessmentResponse)
def save(assessment_id: uuid.UUID, payload: AnswerSave, principal: Annotated[Principal, Depends(require_csrf_roles("student"))], db: Annotated[Session, Depends(get_db)]):
    return assessments.save_answer(db, principal, assessment_id, payload)

@router.post("/{assessment_id}/submit", response_model=AssessmentResponse)
def submit(assessment_id: uuid.UUID, payload: SubmissionRequest, principal: Annotated[Principal, Depends(require_csrf_roles("student"))], db: Annotated[Session, Depends(get_db)]):
    return assessments.submit(db, principal, assessment_id, payload.idempotencyKey)

@router.get("/{assessment_id}/assets/{asset_id}")
def asset(assessment_id: uuid.UUID, asset_id: uuid.UUID,
          principal: Annotated[Principal, Depends(require_roles("student"))],
          db: Annotated[Session, Depends(get_db)], storage: Annotated[ObjectStorage, Depends(get_storage)]):
    document_id = assessments.authorize_asset(db, principal, assessment_id, asset_id)
    stored = documents.download_asset(db, storage, document_id, asset_id)
    return Response(content=stored.content, media_type=stored.content_type,
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})
