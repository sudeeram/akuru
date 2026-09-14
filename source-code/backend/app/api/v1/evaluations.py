import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.evaluations import CorpusCreate, CorpusResponse, CorpusReview, EvaluationDashboard, EvaluationRunCreate, EvaluationRunResponse, ReleaseResponse, ReleaseUpdate
from app.security import Principal
from app.services import evaluations

router = APIRouter(prefix="/evaluations", tags=["evaluations"])

@router.get("/admin", response_model=EvaluationDashboard)
def admin_dashboard(principal: Annotated[Principal, Depends(require_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return evaluations.dashboard(db)

@router.post("/admin/corpora", response_model=CorpusResponse, status_code=status.HTTP_201_CREATED)
def create_corpus(payload: CorpusCreate, principal: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return evaluations.create_corpus(db, principal, payload)

@router.post("/admin/corpora/{corpus_id}/review", response_model=CorpusResponse)
def review_corpus(corpus_id: uuid.UUID, payload: CorpusReview, principal: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return evaluations.review_corpus(db, principal, corpus_id, payload.decision)

@router.post("/admin/runs", response_model=EvaluationRunResponse, status_code=status.HTTP_201_CREATED)
def run_evaluation(payload: EvaluationRunCreate, principal: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return evaluations.run(db, principal, payload)

@router.post("/admin/releases", response_model=ReleaseResponse)
def update_release(payload: ReleaseUpdate, principal: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return evaluations.set_release(db, principal, payload)
