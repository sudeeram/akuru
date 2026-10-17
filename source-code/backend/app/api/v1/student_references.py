"""Student access to explicitly published, enrolled-subject reference PDFs."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.permissions import require_roles
from app.security import Principal
from app.services import reference_materials
from app.storage import ObjectStorage, get_storage

router = APIRouter(prefix="/student/references", tags=["student references"])


@router.get("")
def list_references(principal: Annotated[Principal, Depends(require_roles("student"))],
                    db: Annotated[Session, Depends(get_db)]):
    return {"references": reference_materials.list_for_student(db, principal)}


@router.get("/{document_id}/content")
def read_reference(document_id: uuid.UUID,
                   principal: Annotated[Principal, Depends(require_roles("student"))],
                   db: Annotated[Session, Depends(get_db)],
                   storage: Annotated[ObjectStorage, Depends(get_storage)]):
    stored = reference_materials.content(db, storage, principal, document_id)
    return Response(content=stored.content, media_type="application/pdf",
                    headers={"Content-Disposition": "inline", "Cache-Control": "private, no-store",
                             "X-Content-Type-Options": "nosniff"})
