import hashlib
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import DomainError
from app.models import Assessment, FamilyUsageEvent, StudentProfile


def pseudonymous_student_id(settings: Settings, student_id) -> str:
    secret = settings.operations_token.get_secret_value() if settings.operations_token else settings.database_password
    return hashlib.sha256(f"{secret}:{student_id}".encode()).hexdigest()[:24]


def reserve_assessment(db: Session, settings: Settings, assessment: Assessment, operation_id: str, request_quantity: int) -> None:
    profile = db.get(StudentProfile, assessment.student_id)
    if not profile:
        raise DomainError("family_usage_scope_missing", "The student has no family usage scope.", 409)
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": str(profile.parent_id)})
    start = datetime.now(timezone.utc) - timedelta(days=1)
    totals = dict(db.execute(select(FamilyUsageEvent.kind, func.coalesce(func.sum(FamilyUsageEvent.quantity), 0)).where(
        FamilyUsageEvent.family_id == profile.parent_id, FamilyUsageEvent.created_at >= start
    ).group_by(FamilyUsageEvent.kind)).all())
    if int(totals.get("ai_request", 0)) + request_quantity > settings.family_ai_requests_per_day:
        raise DomainError("family_ai_request_quota", "This family's daily AKURU assessment limit has been reached.", 429)
    if int(totals.get("ai_token", 0)) >= settings.family_ai_tokens_per_day:
        raise DomainError("family_ai_token_budget", "This family's daily AI token budget has been reached.", 429)
    existing = db.scalar(select(FamilyUsageEvent).where(FamilyUsageEvent.family_id == profile.parent_id,
        FamilyUsageEvent.kind == "ai_request", FamilyUsageEvent.operation_id == operation_id))
    if not existing:
        db.add(FamilyUsageEvent(family_id=profile.parent_id, student_id=assessment.student_id,
            kind="ai_request", quantity=request_quantity, operation_id=operation_id))
        db.flush()


def record_tokens(db: Session, assessment: Assessment, operation_id: str, quantity: int) -> None:
    profile = db.get(StudentProfile, assessment.student_id)
    if profile and not db.scalar(select(FamilyUsageEvent).where(FamilyUsageEvent.family_id == profile.parent_id,
        FamilyUsageEvent.kind == "ai_token", FamilyUsageEvent.operation_id == operation_id)):
        db.add(FamilyUsageEvent(family_id=profile.parent_id, student_id=assessment.student_id,
            kind="ai_token", quantity=max(0, quantity), operation_id=operation_id))
