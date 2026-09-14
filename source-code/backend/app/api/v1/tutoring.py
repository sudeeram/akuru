import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.tutor_profiles import (
    TutorAdminPresetsResponse,
    TutorOptionsResponse,
    TutorPresetUpdate,
    TutorProfileInput,
    TutorProfileListResponse,
    TutorProfileResponse,
)
from app.schemas.tutoring import TutorCapabilitiesResponse
from app.security import Principal
from app.services.assessment_access import tutor_capabilities
from app.services import tutor_profiles


router = APIRouter(prefix="/tutoring", tags=["tutoring"])


@router.get("/capabilities", response_model=TutorCapabilitiesResponse)
def capabilities(
    principal: Annotated[Principal, Depends(require_roles("student"))],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    return tutor_capabilities(db, settings, principal.user.id)


@router.get("/options", response_model=TutorOptionsResponse, response_model_exclude_none=True)
def profile_options(
    _principal: Annotated[Principal, Depends(require_roles("student", "parent", "admin"))],
    db: Annotated[Session, Depends(get_db)],
):
    return tutor_profiles.options(db)


@router.get("/profiles", response_model=TutorProfileListResponse)
def profiles(
    principal: Annotated[Principal, Depends(require_roles("student"))],
    db: Annotated[Session, Depends(get_db)],
):
    return tutor_profiles.list_for_student(db, principal.user.id)


@router.post("/profiles", response_model=TutorProfileResponse, status_code=201)
def create_profile(
    payload: TutorProfileInput,
    principal: Annotated[Principal, Depends(require_csrf_roles("student"))],
    db: Annotated[Session, Depends(get_db)],
):
    return tutor_profiles.create(db, principal, payload)


@router.post("/profiles/{profile_ref}", response_model=TutorProfileResponse)
def update_profile(
    profile_ref: str,
    payload: TutorProfileInput,
    principal: Annotated[Principal, Depends(require_csrf_roles("student"))],
    db: Annotated[Session, Depends(get_db)],
):
    return tutor_profiles.update(db, principal, profile_ref, payload)


@router.delete("/profiles/{profile_ref}", status_code=204)
def remove_profile(
    profile_ref: str,
    principal: Annotated[Principal, Depends(require_csrf_roles("student"))],
    db: Annotated[Session, Depends(get_db)],
):
    tutor_profiles.remove(db, principal, profile_ref)


@router.get("/students/{student_id}/profiles", response_model=TutorProfileListResponse)
def visible_profiles(
    student_id: uuid.UUID,
    principal: Annotated[Principal, Depends(require_roles("parent", "admin"))],
    db: Annotated[Session, Depends(get_db)],
):
    return tutor_profiles.list_visible_student(db, principal, student_id)


@router.get("/admin/presets", response_model=TutorAdminPresetsResponse)
def presets(
    _principal: Annotated[Principal, Depends(require_roles("admin"))],
    db: Annotated[Session, Depends(get_db)],
):
    return tutor_profiles.admin_presets(db)


@router.post("/admin/avatars/{code}", response_model=TutorAdminPresetsResponse)
def update_avatar(
    code: str,
    payload: TutorPresetUpdate,
    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
    db: Annotated[Session, Depends(get_db)],
):
    return tutor_profiles.update_avatar(db, principal, code, payload)


@router.post("/admin/voices/{code}", response_model=TutorAdminPresetsResponse)
def update_voice(
    code: str,
    payload: TutorPresetUpdate,
    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
    db: Annotated[Session, Depends(get_db)],
):
    return tutor_profiles.update_voice(db, principal, code, payload)
