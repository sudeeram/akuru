import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.retrieval import EvidenceResponse, ReindexRequest, ReindexResponse, RetrievalRequest, RetrievalResponse
from app.security import Principal
from app.services import retrieval

router = APIRouter(prefix="/retrieval", tags=["retrieval"])

@router.post("/search", response_model=RetrievalResponse)
def search(payload: RetrievalRequest, principal: Annotated[Principal, Depends(require_csrf_roles("admin", "parent", "student"))], db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)]):
    return retrieval.retrieve(db, settings, principal, payload.studentId, payload.subjectId, payload.query, payload.limit)

@router.get("/evidence/{chunk_id}", response_model=EvidenceResponse)
def get_evidence(chunk_id: uuid.UUID, student_id: Annotated[uuid.UUID, Query(alias="studentId")], principal: Annotated[Principal, Depends(require_roles("admin", "parent", "student"))], db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)]):
    return retrieval.evidence(db, principal, settings, chunk_id, student_id)

@router.post("/admin/reindex", response_model=ReindexResponse)
def reindex(payload: ReindexRequest, _principal: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)]):
    return retrieval.reindex_document(db, settings, payload.documentId)
