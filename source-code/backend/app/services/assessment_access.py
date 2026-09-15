import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import DomainError
from app.models import Assessment
from app.schemas.assessments import AssessmentMode


class TutorCapability(StrEnum):
    TEXT = "text"
    VOICE = "voice"
    TOOLS = "tools"


FORMAL_ASSESSMENT_KINDS = frozenset(
    {AssessmentMode.OFFICIAL_PAPER.value, AssessmentMode.MOCK.value}
)
KNOWN_ASSESSMENT_KINDS = frozenset(mode.value for mode in AssessmentMode)


def is_formal_assessment(mode: str) -> bool:
    _validate_mode(mode)
    return mode in FORMAL_ASSESSMENT_KINDS


def require_practice_assistance(mode: str, *, assistance: str = "Hints") -> None:
    """Fail closed when an assessment-mode aid is requested outside practice."""
    _validate_mode(mode)
    if mode != AssessmentMode.PRACTICE.value:
        existing_hint = assistance == "Hints"
        raise DomainError(
            "hints_disabled" if existing_hint else "assistance_disabled_during_formal_assessment",
            "Hints are unavailable during mock and official papers."
            if existing_hint
            else f"{assistance} are available during practice only.",
            403,
        )


def active_formal_assessment(db: Session, student_id: uuid.UUID) -> Assessment | None:
    """Return the student's live formal assessment, ignoring elapsed active rows."""
    now = datetime.now(timezone.utc)
    return db.scalar(
        select(Assessment).where(
            Assessment.student_id == student_id,
            Assessment.status == "active",
            Assessment.ends_at > now,
            Assessment.mode.in_(FORMAL_ASSESSMENT_KINDS),
        )
    )


def tutor_feature_enabled(settings: Settings, capability: TutorCapability) -> bool:
    return {
        TutorCapability.TEXT: settings.tutor_text_enabled,
        TutorCapability.VOICE: settings.tutor_voice_enabled,
        TutorCapability.TOOLS: settings.tutor_tools_enabled,
    }[capability]


def require_tutor_access(
    db: Session,
    settings: Settings,
    student_id: uuid.UUID,
    capability: TutorCapability,
    subject_id: str | None = None,
    workflow: str | None = None,
) -> None:
    """Authorize a tutor capability and block all help during a live formal attempt."""
    if not tutor_feature_enabled(settings, capability):
        raise DomainError(
            "tutor_feature_disabled",
            f"AKURU Tutor {capability.value} is not enabled.",
            403,
        )
    if active_formal_assessment(db, student_id):
        raise DomainError(
            "tutor_disabled_during_formal_assessment",
            "AKURU Tutor is unavailable while a formal assessment is active.",
            403,
        )
    if settings.tutor_release_gates_required and subject_id:
        from app.services.evaluations import tutor_feature_allowed
        release_workflow = workflow or f"tutor_{capability.value}"
        allowed, reason = tutor_feature_allowed(db, subject_id, release_workflow)
        if not allowed:
            raise DomainError("tutor_release_blocked", reason, 403)


def tutor_capabilities(db: Session, settings: Settings, student_id: uuid.UUID) -> dict:
    formal = active_formal_assessment(db, student_id)
    blocked = formal is not None
    reason = "formal_assessment_active" if blocked else None
    return {
        "textEnabled": settings.tutor_text_enabled and not blocked,
        "voiceEnabled": settings.tutor_voice_enabled and not blocked,
        "toolsEnabled": settings.tutor_tools_enabled and not blocked,
        "blockedReason": reason,
    }


def _validate_mode(mode: str) -> None:
    if mode not in KNOWN_ASSESSMENT_KINDS:
        raise DomainError(
            "unknown_assessment_mode",
            "The assessment mode is not recognized; learning assistance is disabled.",
            409,
        )
