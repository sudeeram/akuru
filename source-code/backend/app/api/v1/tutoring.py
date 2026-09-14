from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.permissions import require_roles
from app.schemas.tutoring import TutorCapabilitiesResponse
from app.security import Principal
from app.services.assessment_access import tutor_capabilities


router = APIRouter(prefix="/tutoring", tags=["tutoring"])


@router.get("/capabilities", response_model=TutorCapabilitiesResponse)
def capabilities(
    principal: Annotated[Principal, Depends(require_roles("student"))],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    return tutor_capabilities(db, settings, principal.user.id)
