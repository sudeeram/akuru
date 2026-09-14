import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.permissions import require_roles
from app.schemas.mastery import MasteryResponse
from app.security import Principal
from app.services import mastery


router = APIRouter(prefix="/mastery", tags=["mastery"])

@router.get("/students/{student_id}", response_model=MasteryResponse)
def student_mastery(student_id: uuid.UUID,
                    principal: Annotated[Principal, Depends(require_roles("student", "parent"))],
                    db: Annotated[Session, Depends(get_db)],
                    subject_id: Annotated[str | None, Query(alias="subjectId")] = None):
    return mastery.list_mastery(db, principal, student_id, subject_id)
