from datetime import datetime, timedelta, timezone
import math
import uuid

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import AuditEvent, StudentAIQuota, StudentAIUsage, StudentProfile, User
from app.schemas.tutor_quotas import AdminQuotaUpdate
from app.security import Principal


DEFAULT_REQUESTS = 100
DEFAULT_TEXT_TOKENS = 200000
DEFAULT_VOICE_SECONDS = 3600


def quota_by_ref(db: Session, value: str) -> StudentAIQuota:
    row = db.scalar(select(StudentAIQuota).where(StudentAIQuota.public_ref == value))
    if not row:
        raise DomainError("student_not_found", "Student not found.", 404)
    return row


def ensure(db: Session, student_id: uuid.UUID) -> StudentAIQuota:
    row = db.get(StudentAIQuota, student_id)
    if row:
        return row
    if not db.get(StudentProfile, student_id):
        raise DomainError("student_not_found", "Student not found.", 404)
    row = StudentAIQuota(student_id=student_id, period_days=30, request_allowance=DEFAULT_REQUESTS,
                         text_token_allowance=DEFAULT_TEXT_TOKENS, voice_seconds_allowance=DEFAULT_VOICE_SECONDS)
    db.add(row); db.flush()
    return row


def _period(row: StudentAIQuota) -> tuple[datetime, datetime, bool]:
    now = datetime.now(timezone.utc)
    anchor = row.period_anchor
    if anchor.tzinfo is None:
        anchor = anchor.replace(tzinfo=timezone.utc)
    length = timedelta(days=row.period_days)
    periods = max(0, int((now - anchor) // length))
    start = anchor + periods * length
    return start, start + length, periods > 0


def _totals(db: Session, student_id: uuid.UUID, start: datetime) -> dict[str, int]:
    return {kind: int(value) for kind, value in db.execute(select(
        StudentAIUsage.dimension, func.coalesce(func.sum(StudentAIUsage.quantity), 0)
    ).where(StudentAIUsage.student_id == student_id, StudentAIUsage.created_at >= start)
      .group_by(StudentAIUsage.dimension)).all()}


def _response(db: Session, row: StudentAIQuota) -> dict:
    student = db.get(User, row.student_id)
    start, end, renewed = _period(row); totals = _totals(db, row.student_id, start)
    values = {
        "requests": (row.request_allowance, totals.get("request", 0)),
        "textTokens": (row.text_token_allowance, totals.get("text_token", 0)),
        "voiceMinutes": (row.voice_seconds_allowance // 60, math.ceil(totals.get("voice_second", 0) / 60)),
    }
    shaped = {key: {"allowance": allowance, "used": max(0, used), "remaining": max(0, allowance - used)}
              for key, (allowance, used) in values.items()}
    ratios = [item["remaining"] / item["allowance"] for item in shaped.values() if item["allowance"]]
    exhausted = shaped["requests"]["remaining"] == 0 or shaped["textTokens"]["remaining"] == 0
    voice_exhausted = shaped["voiceMinutes"]["remaining"] == 0
    state = ("disabled" if not row.is_enabled else "exhausted" if exhausted else
             "renewed" if renewed and not any(totals.values()) else
             "warning" if voice_exhausted or (ratios and min(ratios) <= .2) else "available")
    fallback = ("Tutor AI is disabled for this account." if state == "disabled" else
                "Your AI allowance is used up. You can still read saved transcripts and approved resources." if state == "exhausted" else
                "Your voice allowance is used up, but you can continue by text." if voice_exhausted else
                "Your AI allowance is running low." if state == "warning" else
                "Your allowance has renewed for a new period." if state == "renewed" else "Your tutor allowance is available.")
    return {"studentRef": row.public_ref, "studentName": student.display_name,
            "enabled": row.is_enabled, "state": state, "periodDays": row.period_days,
            "periodStartsAt": start, "renewsAt": end, **shaped, "fallbackMessage": fallback}


def student_status(db: Session, principal: Principal) -> dict:
    if principal.user.role != "student":
        raise DomainError("permission_denied", "Student access required.", 403)
    return _response(db, ensure(db, principal.user.id))


def list_admin(db: Session) -> dict:
    students = db.scalars(select(User).where(User.role == "student", User.is_active.is_(True)).order_by(User.display_name)).all()
    return {"quotas": [_response(db, ensure(db, student.id)) for student in students]}


def update_admin(db: Session, principal: Principal, student_ref: str, payload: AdminQuotaUpdate) -> dict:
    existing = quota_by_ref(db, student_ref)
    student_id = existing.student_id
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": str(student_id)})
    row = ensure(db, student_id)
    before = {"periodDays": row.period_days, "requestAllowance": row.request_allowance,
              "textTokenAllowance": row.text_token_allowance, "voiceMinuteAllowance": row.voice_seconds_allowance // 60,
              "enabled": row.is_enabled}
    row.period_days = payload.periodDays; row.request_allowance = payload.requestAllowance
    row.text_token_allowance = payload.textTokenAllowance; row.voice_seconds_allowance = payload.voiceMinuteAllowance * 60
    row.is_enabled = payload.enabled; row.updated_by = principal.user.id
    after = payload.model_dump(exclude={"reason"})
    if before["enabled"] and not payload.enabled:
        change = "disabled"
    elif not before["enabled"] and payload.enabled:
        change = "enabled"
    else:
        old_values = (before["requestAllowance"], before["textTokenAllowance"], before["voiceMinuteAllowance"])
        new_values = (payload.requestAllowance, payload.textTokenAllowance, payload.voiceMinuteAllowance)
        change = ("increased" if all(new >= old for new, old in zip(new_values, old_values)) and new_values != old_values
                  else "reduced" if all(new <= old for new, old in zip(new_values, old_values)) and new_values != old_values
                  else "updated")
    db.add(AuditEvent(actor_id=principal.user.id, action=f"student_ai_quota.{change}",
        target_type="student_ai_quota", target_id=student_ref,
        event_data={"reason": payload.reason, "before": before, "after": after}))
    db.commit(); db.refresh(row)
    return _response(db, row)


def audit_history(db: Session, student_ref: str) -> dict:
    quota_by_ref(db, student_ref)
    rows = db.scalars(select(AuditEvent).where(AuditEvent.target_type == "student_ai_quota",
        AuditEvent.target_id == student_ref).order_by(AuditEvent.created_at.desc()).limit(100)).all()
    return {"studentRef": student_ref, "events": [{"action": row.action,
        "reason": row.event_data.get("reason", ""), "changes": {"before": row.event_data.get("before"), "after": row.event_data.get("after")},
        "createdAt": row.created_at} for row in rows]}


def reserve_text(db: Session, student_id: uuid.UUID, operation_id: str, estimated_tokens: int) -> None:
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": str(student_id)})
    row = ensure(db, student_id)
    existing = db.scalar(select(StudentAIUsage.id).where(StudentAIUsage.student_id == student_id,
        StudentAIUsage.operation_id == operation_id, StudentAIUsage.event_type == "reserve"))
    if existing:
        return
    if not row.is_enabled:
        raise DomainError("student_ai_quota_disabled", "Your AKURU Tutor allowance is disabled. Ask your administrator for help.", 429)
    start, _, _ = _period(row); totals = _totals(db, student_id, start)
    if totals.get("request", 0) + 1 > row.request_allowance:
        raise DomainError("student_ai_request_quota_exhausted", "Your tutor request allowance is used up for this period.", 429)
    if totals.get("text_token", 0) + estimated_tokens > row.text_token_allowance:
        raise DomainError("student_ai_text_quota_exhausted", "Your tutor text allowance is used up for this period. You can still review saved learning material.", 429)
    db.add_all([StudentAIUsage(student_id=student_id, operation_id=operation_id, dimension="request", event_type="reserve", quantity=1),
                StudentAIUsage(student_id=student_id, operation_id=operation_id, dimension="text_token", event_type="reserve", quantity=estimated_tokens)])
    db.flush()


def settle_text(db: Session, student_id: uuid.UUID, operation_id: str, estimated_tokens: int, actual_tokens: int) -> None:
    if not db.scalar(select(StudentAIUsage.id).where(StudentAIUsage.student_id == student_id,
        StudentAIUsage.operation_id == operation_id, StudentAIUsage.dimension == "text_token", StudentAIUsage.event_type == "settle")):
        db.add(StudentAIUsage(student_id=student_id, operation_id=operation_id, dimension="text_token",
            event_type="settle", quantity=max(0, actual_tokens) - estimated_tokens))


def release_text(db: Session, student_id: uuid.UUID, operation_id: str, estimated_tokens: int, reason: str) -> None:
    for dimension, quantity in (("request", -1), ("text_token", -estimated_tokens)):
        if not db.scalar(select(StudentAIUsage.id).where(StudentAIUsage.student_id == student_id,
            StudentAIUsage.operation_id == operation_id, StudentAIUsage.dimension == dimension,
            StudentAIUsage.event_type == "release")):
            db.add(StudentAIUsage(student_id=student_id, operation_id=operation_id, dimension=dimension,
                event_type="release", quantity=quantity, reason=reason))


def reserve_voice(db: Session, student_id: uuid.UUID, operation_id: str, estimated_seconds: int) -> None:
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": str(student_id)})
    row = ensure(db, student_id); start, _, _ = _period(row)
    if not row.is_enabled:
        raise DomainError("student_ai_quota_disabled", "Your AKURU Tutor allowance is disabled.", 429)
    if db.scalar(select(StudentAIUsage.id).where(StudentAIUsage.student_id == student_id,
        StudentAIUsage.operation_id == operation_id, StudentAIUsage.dimension == "voice_second",
        StudentAIUsage.event_type == "reserve")):
        return
    if _totals(db, student_id, start).get("voice_second", 0) + estimated_seconds > row.voice_seconds_allowance:
        raise DomainError("student_ai_voice_quota_exhausted", "Your tutor voice allowance is used up for this period. You can continue with text if text allowance remains.", 429)
    db.add(StudentAIUsage(student_id=student_id, operation_id=operation_id, dimension="voice_second",
                          event_type="reserve", quantity=max(0, estimated_seconds)))
    db.flush()


def available_voice_seconds(db: Session, student_id: uuid.UUID) -> int:
    row = ensure(db, student_id)
    if not row.is_enabled:
        return 0
    start, _, _ = _period(row)
    return max(0, row.voice_seconds_allowance - _totals(db, student_id, start).get("voice_second", 0))


def settle_voice(db: Session, student_id: uuid.UUID, operation_id: str, estimated_seconds: int, actual_seconds: int) -> None:
    if not db.scalar(select(StudentAIUsage.id).where(StudentAIUsage.student_id == student_id,
        StudentAIUsage.operation_id == operation_id, StudentAIUsage.dimension == "voice_second",
        StudentAIUsage.event_type == "settle")):
        db.add(StudentAIUsage(student_id=student_id, operation_id=operation_id, dimension="voice_second",
                              event_type="settle", quantity=max(0, actual_seconds) - estimated_seconds))


def release_voice(db: Session, student_id: uuid.UUID, operation_id: str, estimated_seconds: int, reason: str) -> None:
    if not db.scalar(select(StudentAIUsage.id).where(StudentAIUsage.student_id == student_id,
        StudentAIUsage.operation_id == operation_id, StudentAIUsage.dimension == "voice_second",
        StudentAIUsage.event_type == "release")):
        db.add(StudentAIUsage(student_id=student_id, operation_id=operation_id, dimension="voice_second",
                              event_type="release", quantity=-estimated_seconds, reason=reason))
