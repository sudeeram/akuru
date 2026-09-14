import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import (
    AuditEvent,
    StudentProfile,
    TutorAvatar,
    TutorProfile,
    TutorProfileVersion,
    TutorVoicePreset,
    User,
)
from app.schemas.tutor_profiles import (
    TutorAdminPresetsResponse,
    TutorAvatarResponse,
    TutorOptionsResponse,
    TutorPresetUpdate,
    TutorProfileInput,
    TutorProfileListResponse,
    TutorProfileResponse,
    TutorVoiceResponse,
)
from app.security import Principal


PRESENTATIONS = ["masculine", "feminine", "neutral"]
TONES = ["calm", "encouraging", "direct", "playful"]
LEVELS = ["low", "medium", "high"]
CHARACTERS = ["childlike", "balanced", "authoritative"]
DEPTHS = ["concise", "standard", "detailed"]
TEACHING_STYLES = ["guided", "socratic", "example_led", "exam_focused"]


def _avatar_response(row: TutorAvatar, *, admin: bool = False) -> TutorAvatarResponse:
    return TutorAvatarResponse(
        code=row.code,
        name=row.display_name,
        description=row.description,
        imagePath=row.image_path,
        presentation=row.presentation,
        enabled=row.is_enabled,
        sortOrder=row.sort_order if admin else None,
    )


def _voice_response(row: TutorVoicePreset, *, admin: bool = False) -> TutorVoiceResponse:
    return TutorVoiceResponse(
        code=row.code,
        name=row.display_name,
        description=row.description,
        presentation=row.presentation,
        enabled=row.is_enabled,
        sortOrder=row.sort_order if admin else None,
    )


def options(db: Session) -> TutorOptionsResponse:
    avatars = db.scalars(select(TutorAvatar).order_by(TutorAvatar.sort_order, TutorAvatar.code)).all()
    voices = db.scalars(select(TutorVoicePreset).order_by(TutorVoicePreset.sort_order, TutorVoicePreset.code)).all()
    return TutorOptionsResponse(
        presentations=PRESENTATIONS,
        tones=TONES,
        levels=LEVELS,
        communicationCharacters=CHARACTERS,
        explanationDepths=DEPTHS,
        teachingStyles=TEACHING_STYLES,
        avatars=[_avatar_response(row) for row in avatars],
        voices=[_voice_response(row) for row in voices],
    )


def admin_presets(db: Session) -> TutorAdminPresetsResponse:
    avatars = db.scalars(select(TutorAvatar).order_by(TutorAvatar.sort_order, TutorAvatar.code)).all()
    voices = db.scalars(
        select(TutorVoicePreset).order_by(TutorVoicePreset.sort_order, TutorVoicePreset.code)
    ).all()
    return TutorAdminPresetsResponse(
        avatars=[_avatar_response(row, admin=True) for row in avatars],
        voices=[_voice_response(row, admin=True) for row in voices],
    )


def _version(db: Session, profile: TutorProfile) -> TutorProfileVersion:
    row = db.scalar(
        select(TutorProfileVersion).where(
            TutorProfileVersion.profile_id == profile.id,
            TutorProfileVersion.version_number == profile.current_version_number,
        )
    )
    if not row:
        raise DomainError("tutor_profile_invalid", "The tutor profile has no current version.", 409)
    return row


def _profile_response(db: Session, profile: TutorProfile) -> TutorProfileResponse:
    row = _version(db, profile)
    return TutorProfileResponse(
        profileRef=profile.public_ref,
        version=row.version_number,
        active=profile.is_active,
        name=row.name,
        presentation=row.presentation,
        avatarCode=row.avatar_code,
        voiceCode=row.voice_code,
        tone=row.tone,
        friendliness=row.friendliness,
        enthusiasm=row.enthusiasm,
        speed=row.speed,
        communicationCharacter=row.communication_character,
        explanationDepth=row.explanation_depth,
        teachingStyle=row.teaching_style,
    )


def _validate_presets(db: Session, payload: TutorProfileInput) -> None:
    avatar = db.get(TutorAvatar, payload.avatarCode)
    if not avatar or not avatar.is_enabled:
        raise DomainError("tutor_avatar_unavailable", "Choose an available tutor avatar.", 422)
    voice = db.get(TutorVoicePreset, payload.voiceCode)
    if not voice or not voice.is_enabled:
        raise DomainError("tutor_voice_unavailable", "Choose an available tutor voice.", 422)
    if avatar.presentation not in {payload.presentation, "neutral"}:
        raise DomainError(
            "tutor_avatar_presentation_mismatch",
            "Choose an avatar that matches the tutor presentation.",
            422,
        )
    if voice.presentation not in {payload.presentation, "neutral"}:
        raise DomainError(
            "tutor_voice_presentation_mismatch",
            "Choose a voice that matches the tutor presentation.",
            422,
        )


def list_for_student(db: Session, student_id: uuid.UUID) -> TutorProfileListResponse:
    profiles = db.scalars(
        select(TutorProfile).where(
            TutorProfile.student_id == student_id,
            TutorProfile.is_active.is_(True),
        ).order_by(TutorProfile.created_at, TutorProfile.public_ref)
    ).all()
    return TutorProfileListResponse(profiles=[_profile_response(db, row) for row in profiles])


def list_visible_student(
    db: Session, principal: Principal, student_id: uuid.UUID
) -> TutorProfileListResponse:
    student = db.get(User, student_id)
    profile = db.get(StudentProfile, student_id)
    if not student or student.role != "student" or not profile:
        raise DomainError("student_not_found", "Student not found.", 404)
    if principal.user.role == "parent" and profile.parent_id != principal.user.id:
        raise DomainError("student_not_found", "Student not found.", 404)
    return list_for_student(db, student_id)


def _owned_profile(db: Session, student_id: uuid.UUID, public_ref: str, *, lock: bool = False) -> TutorProfile:
    query = select(TutorProfile).where(
        TutorProfile.public_ref == public_ref,
        TutorProfile.student_id == student_id,
        TutorProfile.is_active.is_(True),
    )
    row = db.scalar(query.with_for_update() if lock else query)
    if not row:
        raise DomainError("tutor_profile_not_found", "Tutor profile not found.", 404)
    return row


def _add_version(
    db: Session,
    profile: TutorProfile,
    actor_id: uuid.UUID,
    payload: TutorProfileInput,
    version_number: int,
) -> None:
    db.add(
        TutorProfileVersion(
            profile_id=profile.id,
            version_number=version_number,
            name=payload.name,
            presentation=payload.presentation,
            avatar_code=payload.avatarCode,
            voice_code=payload.voiceCode,
            tone=payload.tone,
            friendliness=payload.friendliness,
            enthusiasm=payload.enthusiasm,
            speed=payload.speed,
            communication_character=payload.communicationCharacter,
            explanation_depth=payload.explanationDepth,
            teaching_style=payload.teachingStyle,
            created_by=actor_id,
        )
    )


def create(db: Session, principal: Principal, payload: TutorProfileInput) -> TutorProfileResponse:
    _validate_presets(db, payload)
    profile = TutorProfile(
        public_ref=f"tutor_{uuid.uuid4().hex[:24]}",
        student_id=principal.user.id,
        current_version_number=1,
    )
    db.add(profile)
    db.flush()
    _add_version(db, profile, principal.user.id, payload, 1)
    db.add(
        AuditEvent(
            actor_id=principal.user.id,
            action="tutor_profile.created",
            target_type="tutor_profile",
            target_id=profile.public_ref,
            event_data={"version": 1, "avatarCode": payload.avatarCode, "voiceCode": payload.voiceCode},
        )
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DomainError("tutor_profile_conflict", "The tutor profile could not be created.", 409) from exc
    db.refresh(profile)
    return _profile_response(db, profile)


def update(
    db: Session,
    principal: Principal,
    public_ref: str,
    payload: TutorProfileInput,
) -> TutorProfileResponse:
    _validate_presets(db, payload)
    profile = _owned_profile(db, principal.user.id, public_ref, lock=True)
    next_version = profile.current_version_number + 1
    _add_version(db, profile, principal.user.id, payload, next_version)
    profile.current_version_number = next_version
    db.add(
        AuditEvent(
            actor_id=principal.user.id,
            action="tutor_profile.updated",
            target_type="tutor_profile",
            target_id=profile.public_ref,
            event_data={"version": next_version, "avatarCode": payload.avatarCode, "voiceCode": payload.voiceCode},
        )
    )
    db.commit()
    db.refresh(profile)
    return _profile_response(db, profile)


def remove(db: Session, principal: Principal, public_ref: str) -> None:
    profile = _owned_profile(db, principal.user.id, public_ref, lock=True)
    profile.is_active = False
    db.add(
        AuditEvent(
            actor_id=principal.user.id,
            action="tutor_profile.removed",
            target_type="tutor_profile",
            target_id=profile.public_ref,
            event_data={"version": profile.current_version_number},
        )
    )
    db.commit()


def update_avatar(
    db: Session, principal: Principal, code: str, payload: TutorPresetUpdate
) -> TutorAdminPresetsResponse:
    row = db.get(TutorAvatar, code)
    if not row:
        raise DomainError("tutor_avatar_not_found", "Tutor avatar not found.", 404)
    row.is_enabled = payload.enabled
    row.sort_order = payload.sortOrder
    _audit_preset(db, principal, "avatar", code, payload)
    db.commit()
    return admin_presets(db)


def update_voice(
    db: Session, principal: Principal, code: str, payload: TutorPresetUpdate
) -> TutorAdminPresetsResponse:
    row = db.get(TutorVoicePreset, code)
    if not row:
        raise DomainError("tutor_voice_not_found", "Tutor voice not found.", 404)
    row.is_enabled = payload.enabled
    row.sort_order = payload.sortOrder
    _audit_preset(db, principal, "voice", code, payload)
    db.commit()
    return admin_presets(db)


def _audit_preset(
    db: Session,
    principal: Principal,
    kind: str,
    code: str,
    payload: TutorPresetUpdate,
) -> None:
    db.add(
        AuditEvent(
            actor_id=principal.user.id,
            action=f"tutor_{kind}.updated",
            target_type=f"tutor_{kind}",
            target_id=code,
            event_data={"enabled": payload.enabled, "sortOrder": payload.sortOrder},
        )
    )
