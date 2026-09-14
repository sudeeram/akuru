import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import DomainError
from app.models import (
    AuditEvent, Subject, TextbookUnit, TutorProfile, TutorProfileVersion, TutorSession,
    TutorPractice, TutorSessionProfileEvent, TutorSessionUnitEvent, TutorTurn, TutorTurnSource,
)
from app.schemas.curriculum_plans import PlanUnitResponse
from app.schemas.tutor_sessions import (
    TutorProfileEventResponse, TutorSessionOptionsResponse, TutorSessionResponse,
    TutorSessionSubjectOption, TutorTurnResponse, TutorUnitEventResponse,
)
from app.security import Principal
from app.services import curriculum_plans, tutor_profiles
from app.services.assessment_access import TutorCapability, require_tutor_access


def _uuid(value: str, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as error:
        raise DomainError("invalid_tutor_session_input", f"{field} is invalid.", 422) from error


def _owned_profile(db: Session, student_id: uuid.UUID, public_ref: str) -> tuple[TutorProfile, TutorProfileVersion]:
    profile = db.scalar(select(TutorProfile).where(
        TutorProfile.public_ref == public_ref, TutorProfile.student_id == student_id,
        TutorProfile.is_active.is_(True),
    ))
    if not profile:
        raise DomainError("tutor_profile_not_found", "Tutor profile not found.", 404)
    version = db.scalar(select(TutorProfileVersion).where(
        TutorProfileVersion.profile_id == profile.id,
        TutorProfileVersion.version_number == profile.current_version_number,
    ))
    if not version:
        raise DomainError("tutor_profile_invalid", "The tutor profile has no current version.", 409)
    return profile, version


def _eligible_unit(db: Session, student_id: uuid.UUID, subject_id: str, unit_id: str) -> TextbookUnit:
    coverage = curriculum_plans.student_coverage(db, student_id, subject_id)
    if coverage.status != "ready":
        raise DomainError("tutor_coverage_not_ready", coverage.message, 409)
    eligible = {item.id for item in coverage.coveredUnits}
    if unit_id not in eligible:
        raise DomainError("tutor_unit_not_eligible", "Choose a unit covered for your current Grade and Term.", 422)
    unit = db.get(TextbookUnit, _uuid(unit_id, "Unit"))
    if not unit or unit.subject_id != subject_id:
        raise DomainError("tutor_unit_not_eligible", "Choose an eligible unit in this subject.", 422)
    return unit


def options(db: Session, student_id: uuid.UUID) -> TutorSessionOptionsResponse:
    subjects = db.scalars(select(Subject).order_by(Subject.name)).all()
    available = []
    for subject in subjects:
        try:
            coverage = curriculum_plans.student_coverage(db, student_id, subject.id)
        except DomainError:
            continue
        if coverage.status == "ready" and coverage.coveredUnits:
            available.append(TutorSessionSubjectOption(id=subject.id, name=subject.name, units=coverage.coveredUnits))
    return TutorSessionOptionsResponse(
        subjects=available,
        profiles=tutor_profiles.list_for_student(db, student_id).profiles,
    )


def _owned_session(db: Session, student_id: uuid.UUID, session_ref: str, *, lock: bool = False) -> TutorSession:
    query = select(TutorSession).where(
        TutorSession.public_ref == session_ref, TutorSession.student_id == student_id,
    )
    row = db.scalar(query.with_for_update() if lock else query)
    if not row:
        raise DomainError("tutor_session_not_found", "Tutor session not found.", 404)
    return row


def _require_active(row: TutorSession) -> None:
    if row.status != "active":
        raise DomainError("tutor_session_ended", "This tutor session has ended.", 409)


def _unit_response(unit: TextbookUnit) -> PlanUnitResponse:
    return PlanUnitResponse(id=str(unit.id), code=unit.unit_code, title=unit.title)


def _version_details(db: Session, version_id: uuid.UUID) -> tuple[TutorProfile, TutorProfileVersion]:
    version = db.get(TutorProfileVersion, version_id)
    profile = db.get(TutorProfile, version.profile_id) if version else None
    if not version or not profile:
        raise DomainError("tutor_profile_invalid", "A retained tutor version could not be loaded.", 409)
    return profile, version


def response(db: Session, row: TutorSession) -> TutorSessionResponse:
    unit = db.get(TextbookUnit, row.active_unit_id)
    profile, selected_version = _version_details(db, row.current_profile_version_id)
    turns = db.scalars(select(TutorTurn).where(TutorTurn.session_id == row.id).order_by(TutorTurn.sequence)).all()
    turn_responses = []
    for turn in turns:
        turn_profile, turn_version = _version_details(db, turn.profile_version_id)
        source_count = db.scalar(select(func.count()).select_from(TutorTurnSource).where(TutorTurnSource.turn_id == turn.id)) or 0
        turn_responses.append(TutorTurnResponse(
            turnRef=turn.public_ref, role=turn.role, modality=turn.modality, content=turn.content,
            sequence=turn.sequence, profileRef=turn_profile.public_ref,
            profileVersion=turn_version.version_number,
            sources=["authorized-source" for _ in range(source_count)], createdAt=turn.created_at,
            structured=turn.response_data,
        ))
    profile_events = []
    for event in db.scalars(select(TutorSessionProfileEvent).where(TutorSessionProfileEvent.session_id == row.id).order_by(TutorSessionProfileEvent.created_at, TutorSessionProfileEvent.id)).all():
        old_profile, old_version = _version_details(db, event.from_profile_version_id)
        new_profile, new_version = _version_details(db, event.to_profile_version_id)
        profile_events.append(TutorProfileEventResponse(
            fromProfileRef=old_profile.public_ref, fromProfileVersion=old_version.version_number,
            toProfileRef=new_profile.public_ref, toProfileVersion=new_version.version_number,
            handoverSummary=event.handover_summary, createdAt=event.created_at,
        ))
    unit_events = []
    for event in db.scalars(select(TutorSessionUnitEvent).where(TutorSessionUnitEvent.session_id == row.id).order_by(TutorSessionUnitEvent.created_at, TutorSessionUnitEvent.id)).all():
        unit_events.append(TutorUnitEventResponse(fromUnit=_unit_response(db.get(TextbookUnit, event.from_unit_id)), toUnit=_unit_response(db.get(TextbookUnit, event.to_unit_id)), createdAt=event.created_at))
    return TutorSessionResponse(
        sessionRef=row.public_ref, subjectId=row.subject_id, activeUnit=_unit_response(unit),
        currentTutor=tutor_profiles.profile_version_response(profile, selected_version), mode=row.mode, status=row.status,
        startedAt=row.started_at, endedAt=row.ended_at, turns=turn_responses,
        profileEvents=profile_events, unitEvents=unit_events,
    )


def list_sessions(db: Session, student_id: uuid.UUID):
    rows = db.scalars(select(TutorSession).where(TutorSession.student_id == student_id).order_by(TutorSession.started_at.desc())).all()
    return {"sessions": [response(db, row) for row in rows]}


def start(db: Session, settings: Settings, principal: Principal, payload) -> TutorSessionResponse:
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TEXT)
    existing = db.scalar(select(TutorSession).where(
        TutorSession.student_id == principal.user.id, TutorSession.start_request_key == payload.requestKey,
    ))
    if existing:
        return response(db, existing)
    active = db.scalar(select(TutorSession).where(TutorSession.student_id == principal.user.id, TutorSession.status == "active"))
    if active:
        raise DomainError("tutor_session_already_active", "End your current tutor session before starting another.", 409)
    _, version = _owned_profile(db, principal.user.id, payload.profileRef)
    unit = _eligible_unit(db, principal.user.id, payload.subjectId, payload.unitId)
    row = TutorSession(public_ref=f"tutor_session_{uuid.uuid4().hex}", student_id=principal.user.id,
                       subject_id=payload.subjectId, active_unit_id=unit.id,
                       current_profile_version_id=version.id, start_request_key=payload.requestKey)
    db.add(row)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        replay = db.scalar(select(TutorSession).where(TutorSession.student_id == principal.user.id, TutorSession.start_request_key == payload.requestKey))
        if replay:
            return response(db, replay)
        raise DomainError("tutor_session_already_active", "End your current tutor session before starting another.", 409) from error
    db.refresh(row)
    return response(db, row)


def add_turn(db: Session, settings: Settings, principal: Principal, session_ref: str, payload) -> TutorSessionResponse:
    capability = TutorCapability.VOICE if payload.modality == "voice" else TutorCapability.TEXT
    require_tutor_access(db, settings, principal.user.id, capability)
    row = _owned_session(db, principal.user.id, session_ref, lock=True); _require_active(row)
    replay = db.scalar(select(TutorTurn).where(TutorTurn.session_id == row.id, TutorTurn.request_key == payload.requestKey))
    if replay:
        return response(db, row)
    sequence = (db.scalar(select(func.max(TutorTurn.sequence)).where(TutorTurn.session_id == row.id)) or 0) + 1
    db.add(TutorTurn(public_ref=f"tutor_turn_{uuid.uuid4().hex}", session_id=row.id,
                     profile_version_id=row.current_profile_version_id, sequence=sequence, role="student",
                     modality=payload.modality, content=payload.content.strip(), request_key=payload.requestKey))
    db.commit(); db.refresh(row)
    return response(db, row)


def _handover(db: Session, row: TutorSession) -> dict:
    unit = db.get(TextbookUnit, row.active_unit_id)
    turns = db.scalars(select(TutorTurn).where(TutorTurn.session_id == row.id).order_by(TutorTurn.sequence.desc()).limit(6)).all()
    recent = [{"role": item.role, "summary": " ".join(item.content.split())[:240]} for item in reversed(turns)]
    return {"subjectId": row.subject_id, "unit": {"code": unit.unit_code, "title": unit.title},
            "practiceState": "active", "retainedTurnCount": len(turns), "recentContext": recent}


def switch_profile(db: Session, settings: Settings, principal: Principal, session_ref: str, payload) -> TutorSessionResponse:
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TEXT)
    row = _owned_session(db, principal.user.id, session_ref, lock=True); _require_active(row)
    replay = db.scalar(select(TutorSessionProfileEvent).where(TutorSessionProfileEvent.session_id == row.id, TutorSessionProfileEvent.request_key == payload.requestKey))
    if replay:
        return response(db, row)
    _, version = _owned_profile(db, principal.user.id, payload.profileRef)
    if version.id == row.current_profile_version_id:
        raise DomainError("tutor_profile_already_selected", "That tutor is already leading this session.", 409)
    event = TutorSessionProfileEvent(session_id=row.id, from_profile_version_id=row.current_profile_version_id,
        to_profile_version_id=version.id, request_key=payload.requestKey, handover_summary=_handover(db, row))
    db.add(event); row.current_profile_version_id = version.id
    db.commit(); db.refresh(row)
    return response(db, row)


def switch_unit(db: Session, settings: Settings, principal: Principal, session_ref: str, payload) -> TutorSessionResponse:
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TEXT)
    row = _owned_session(db, principal.user.id, session_ref, lock=True); _require_active(row)
    replay = db.scalar(select(TutorSessionUnitEvent).where(TutorSessionUnitEvent.session_id == row.id, TutorSessionUnitEvent.request_key == payload.requestKey))
    if replay:
        return response(db, row)
    active_practice = db.scalar(select(TutorPractice).where(
        TutorPractice.session_id == row.id, TutorPractice.status == "active"))
    if active_practice:
        raise DomainError("tutor_practice_active", "Submit the active guided-practice question before moving units.", 409)
    unit = _eligible_unit(db, principal.user.id, row.subject_id, payload.unitId)
    if unit.id == row.active_unit_id:
        raise DomainError("tutor_unit_already_selected", "That unit is already active.", 409)
    db.add(TutorSessionUnitEvent(session_id=row.id, from_unit_id=row.active_unit_id, to_unit_id=unit.id, request_key=payload.requestKey))
    row.active_unit_id = unit.id
    db.commit(); db.refresh(row)
    return response(db, row)


def end(db: Session, settings: Settings, principal: Principal, session_ref: str, payload) -> TutorSessionResponse:
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TEXT)
    row = _owned_session(db, principal.user.id, session_ref, lock=True)
    if row.status == "ended":
        if row.end_request_key == payload.requestKey:
            return response(db, row)
        raise DomainError("tutor_session_ended", "This tutor session has ended.", 409)
    row.status = "ended"; row.ended_at = datetime.now(timezone.utc); row.end_request_key = payload.requestKey
    db.add(AuditEvent(actor_id=principal.user.id, action="tutor_session.ended", target_type="tutor_session", target_id=row.public_ref, event_data={"subjectId": row.subject_id}))
    db.commit(); db.refresh(row)
    return response(db, row)
