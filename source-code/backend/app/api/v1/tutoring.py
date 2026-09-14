import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
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
from app.schemas.tutor_sessions import (
    TutorEndSessionRequest, TutorSessionListResponse, TutorSessionOptionsResponse,
    TutorSessionResponse, TutorSessionStartRequest, TutorSwitchProfileRequest,
    TutorSwitchUnitRequest, TutorTurnCreateRequest,
)
from app.schemas.tutor_context import LearnerContextRequest, LearnerContextResponse
from app.schemas.tutor_recommendations import NextUnitRequest, NextUnitResponse
from app.schemas.tutor_sources import TutorCitation, TutorCitationContextResponse, TutorSourceSearchRequest, TutorSourceSearchResponse
from app.security import Principal
from app.services.assessment_access import tutor_capabilities
from app.services import tutor_context, tutor_profiles, tutor_recommendations, tutor_sessions, tutor_sources
from app.storage.base import ObjectStorage
from app.storage.factory import get_storage


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


@router.get("/session-options", response_model=TutorSessionOptionsResponse)
def session_options(
    principal: Annotated[Principal, Depends(require_roles("student"))],
    db: Annotated[Session, Depends(get_db)],
):
    return tutor_sessions.options(db, principal.user.id)


@router.get("/sessions", response_model=TutorSessionListResponse)
def sessions(
    principal: Annotated[Principal, Depends(require_roles("student"))],
    db: Annotated[Session, Depends(get_db)],
):
    return tutor_sessions.list_sessions(db, principal.user.id)


@router.post("/sessions", response_model=TutorSessionResponse, status_code=201)
def start_session(
    payload: TutorSessionStartRequest,
    principal: Annotated[Principal, Depends(require_csrf_roles("student"))],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    return tutor_sessions.start(db, settings, principal, payload)


@router.get("/sessions/{session_ref}", response_model=TutorSessionResponse)
def get_session(
    session_ref: str,
    principal: Annotated[Principal, Depends(require_roles("student"))],
    db: Annotated[Session, Depends(get_db)],
):
    return tutor_sessions.response(db, tutor_sessions._owned_session(db, principal.user.id, session_ref))


@router.post("/sessions/{session_ref}/turns", response_model=TutorSessionResponse)
def add_turn(
    session_ref: str, payload: TutorTurnCreateRequest,
    principal: Annotated[Principal, Depends(require_csrf_roles("student"))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)],
):
    return tutor_sessions.add_turn(db, settings, principal, session_ref, payload)


@router.post("/sessions/{session_ref}/learner-context", response_model=LearnerContextResponse)
def learner_context(
    session_ref: str, payload: LearnerContextRequest,
    principal: Annotated[Principal, Depends(require_csrf_roles("student"))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)],
):
    return tutor_context.build_and_log(db, settings, principal, session_ref, payload.requestKey)


@router.post("/sessions/{session_ref}/next-unit", response_model=NextUnitResponse)
def next_unit(
    session_ref: str, payload: NextUnitRequest,
    principal: Annotated[Principal, Depends(require_csrf_roles("student"))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)],
):
    return tutor_recommendations.recommend(
        db, settings, principal, session_ref, payload.subjectId, payload.requestKey
    )


@router.post("/sessions/{session_ref}/sources/search", response_model=TutorSourceSearchResponse)
def search_sources(
    session_ref: str, payload: TutorSourceSearchRequest,
    principal: Annotated[Principal, Depends(require_csrf_roles("student"))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)],
):
    return tutor_sources.search(db, settings, principal, session_ref, payload.query,
                                payload.textbookEdition, payload.limit)


@router.get("/sessions/{session_ref}/sources/{citation_ref}", response_model=TutorCitation)
def citation(
    session_ref: str, citation_ref: str,
    principal: Annotated[Principal, Depends(require_roles("student"))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)],
):
    return tutor_sources.get_citation(db, settings, principal, session_ref, citation_ref)


@router.get("/sessions/{session_ref}/sources/{citation_ref}/context", response_model=TutorCitationContextResponse)
def citation_context(
    session_ref: str, citation_ref: str,
    principal: Annotated[Principal, Depends(require_roles("student"))],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    radius: Annotated[int, Query(ge=1, le=4)] = 2,
):
    return tutor_sources.nearby_context(db, settings, principal, session_ref, citation_ref, radius)


@router.get("/sessions/{session_ref}/sources/{citation_ref}/asset")
def citation_asset(
    session_ref: str, citation_ref: str,
    principal: Annotated[Principal, Depends(require_roles("student"))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)],
    storage: Annotated[ObjectStorage, Depends(get_storage)],
) -> Response:
    stored = tutor_sources.open_asset(db, settings, principal, storage, session_ref, citation_ref)
    return Response(content=stored.content, media_type=stored.content_type,
                    headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.post("/sessions/{session_ref}/switch-profile", response_model=TutorSessionResponse)
def switch_profile(
    session_ref: str, payload: TutorSwitchProfileRequest,
    principal: Annotated[Principal, Depends(require_csrf_roles("student"))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)],
):
    return tutor_sessions.switch_profile(db, settings, principal, session_ref, payload)


@router.post("/sessions/{session_ref}/switch-unit", response_model=TutorSessionResponse)
def switch_unit(
    session_ref: str, payload: TutorSwitchUnitRequest,
    principal: Annotated[Principal, Depends(require_csrf_roles("student"))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)],
):
    return tutor_sessions.switch_unit(db, settings, principal, session_ref, payload)


@router.post("/sessions/{session_ref}/end", response_model=TutorSessionResponse)
def end_session(
    session_ref: str, payload: TutorEndSessionRequest,
    principal: Annotated[Principal, Depends(require_csrf_roles("student"))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)],
):
    return tutor_sessions.end(db, settings, principal, session_ref, payload)


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
