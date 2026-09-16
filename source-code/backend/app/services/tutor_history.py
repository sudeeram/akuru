import re
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import (AIInvocation, AuditEvent, StudentProfile, TextbookGroup, TextbookTopic, TextbookUnit, TutorPractice,
                        TutorSafetyEvent, TutorSession, TutorSessionSummary, TutorSessionUnitEvent,
                        TutorSessionTopicEvent, TutorSignal, TutorTurn, User)
from app.security import Principal


SAFETY_PATTERNS = (
    ("self_harm", "critical", re.compile(r"\b(kill myself|suicide|hurt myself|self[- ]harm)\b", re.I), "Escalated for immediate parent attention"),
    ("abuse", "high", re.compile(r"\b(abused|someone hurts me|unsafe at home)\b", re.I), "Escalated for parent attention"),
    ("violence", "high", re.compile(r"\b(kill someone|hurt someone|weapon attack)\b", re.I), "Escalated for parent attention"),
)


def detect_safety(db: Session, session: TutorSession, turn: TutorTurn) -> None:
    if turn.role != "student": return
    profile = db.get(StudentProfile, session.student_id)
    for category, severity, pattern, action in SAFETY_PATTERNS:
        if not pattern.search(turn.content): continue
        exists = db.scalar(select(TutorSafetyEvent.id).where(
            TutorSafetyEvent.source_turn_id == turn.id, TutorSafetyEvent.category == category))
        if not exists:
            db.add(TutorSafetyEvent(public_ref=f"safety_{uuid.uuid4().hex}", student_id=session.student_id,
                parent_id=profile.parent_id, session_id=session.id, source_turn_id=turn.id,
                category=category, severity=severity, action=action,
                notification_status="notified", notified_at=datetime.now(timezone.utc)))


def create_summary(db: Session, session: TutorSession) -> TutorSessionSummary:
    existing = db.scalar(select(TutorSessionSummary).where(TutorSessionSummary.session_id == session.id))
    if existing: return existing
    unit_ids = [session.active_unit_id] if session.active_unit_id else []
    for event in db.scalars(select(TutorSessionUnitEvent).where(TutorSessionUnitEvent.session_id == session.id)).all():
        unit_ids.extend((event.from_unit_id, event.to_unit_id))
    units = [db.get(TextbookUnit, value) for value in dict.fromkeys(unit_ids)]
    topic_ids = [session.active_topic_id] if session.active_topic_id else []
    for event in db.scalars(select(TutorSessionTopicEvent).where(TutorSessionTopicEvent.session_id == session.id)).all():
        topic_ids.extend((event.from_topic_id,event.to_topic_id))
    topics=[db.get(TextbookTopic,value) for value in dict.fromkeys(topic_ids)]
    signals = db.scalars(select(TutorSignal).where(TutorSignal.session_id == session.id)).all()
    practices = db.scalars(select(TutorPractice).where(TutorPractice.session_id == session.id)).all()
    ai = db.execute(
        select(func.count(AIInvocation.id), func.coalesce(func.sum(AIInvocation.total_tokens), 0))
        .where(
            AIInvocation.actor_id == session.student_id,
            AIInvocation.purpose == "tutoring",
            AIInvocation.status == "completed",
            AIInvocation.request_metadata["sessionRef"].as_string() == session.public_ref,
        )
    ).one()
    strengths = [s.observation for s in signals if s.category in {"confidence", "engagement"}]
    difficulties = [s.observation for s in signals if s.category in {"misconception", "practice_need"}]
    units = [unit for unit in units if unit]
    next_steps = [f"Continue guided practice for {unit.unit_code} · {unit.title}." for unit in units[:3]]
    next_steps += [f"Continue guided practice for {topic.code} · {topic.title}." for topic in topics[:3]]
    row = TutorSessionSummary(public_ref=f"summary_{uuid.uuid4().hex}", session_id=session.id,
        student_id=session.student_id, subject_id=session.subject_id,
        units_covered=[{"code": unit.unit_code, "title": unit.title} for unit in units] +
            [{"code": topic.code,"title": topic.title,"topicRef":topic.public_ref,
              "groupTitle":db.get(TextbookGroup,topic.group_id).title} for topic in topics],
        activities=["Tutor conversation"] + (["Guided practice"] if practices else []),
        strengths=strengths, difficulties=difficulties, next_steps=next_steps,
        usage_data={"aiRequests": int(ai[0]), "textTokens": int(ai[1]), "voiceTurns": db.scalar(select(func.count()).select_from(TutorTurn).where(TutorTurn.session_id == session.id, TutorTurn.modality == "voice")) or 0})
    db.add(row); db.flush(); return row


def _summary(db: Session, row: TutorSessionSummary) -> dict:
    session = db.get(TutorSession, row.session_id); student = db.get(User, row.student_id)
    return {"summaryRef": row.public_ref, "sessionRef": session.public_ref, "studentName": student.display_name,
        "subjectId": row.subject_id, "unitsCovered": row.units_covered, "activities": row.activities,
        "strengths": row.strengths, "difficulties": row.difficulties, "suggestedNextSteps": row.next_steps,
        "usage": row.usage_data, "createdAt": row.created_at}


def summaries(db: Session, principal: Principal) -> dict:
    query = select(TutorSessionSummary)
    if principal.user.role == "parent":
        children = select(StudentProfile.student_id).where(StudentProfile.parent_id == principal.user.id)
        query = query.where(TutorSessionSummary.student_id.in_(children))
    elif principal.user.role != "admin":
        raise DomainError("permission_denied", "Parent or Admin access required.", 403)
    rows = db.scalars(query.order_by(TutorSessionSummary.created_at.desc())).all()
    return {"summaries": [_summary(db, row) for row in rows]}


def _event(db: Session, row: TutorSafetyEvent) -> dict:
    return {"eventRef": row.public_ref, "studentName": db.get(User, row.student_id).display_name,
        "category": row.category, "severity": row.severity, "action": row.action,
        "notificationStatus": row.notification_status, "reviewStatus": row.review_status, "createdAt": row.created_at}


def safety_events(db: Session, principal: Principal) -> dict:
    query = select(TutorSafetyEvent)
    if principal.user.role == "parent": query = query.where(TutorSafetyEvent.parent_id == principal.user.id)
    elif principal.user.role != "admin": raise DomainError("permission_denied", "Parent or Admin access required.", 403)
    return {"events": [_event(db, row) for row in db.scalars(query.order_by(TutorSafetyEvent.created_at.desc())).all()]}


def review_safety(db: Session, principal: Principal, event_ref: str, status: str, note: str) -> dict:
    row = db.scalar(select(TutorSafetyEvent).where(TutorSafetyEvent.public_ref == event_ref).with_for_update())
    if not row: raise DomainError("safety_event_not_found", "Safety event not found.", 404)
    row.review_status=status; row.review_note=note; row.reviewed_by=principal.user.id; row.reviewed_at=datetime.now(timezone.utc)
    db.add(AuditEvent(actor_id=principal.user.id, action="tutor_safety.reviewed", target_type="tutor_safety_event",
        target_id=row.public_ref, event_data={"status": status, "note": note})); db.commit(); return _event(db, row)


def support_transcript(db: Session, principal: Principal, session_ref: str, reason: str) -> dict:
    session = db.scalar(select(TutorSession).where(TutorSession.public_ref == session_ref))
    if not session: raise DomainError("tutor_session_not_found", "Tutor session not found.", 404)
    turns = db.scalars(select(TutorTurn).where(TutorTurn.session_id == session.id).order_by(TutorTurn.sequence)).all()
    db.add(AuditEvent(actor_id=principal.user.id, action="tutor_transcript.support_accessed", target_type="tutor_session",
        target_id=session_ref, event_data={"reason": reason, "turnCount": len(turns)})); db.commit()
    return {"sessionRef": session_ref, "studentName": db.get(User, session.student_id).display_name,
        "turns": [{"turnRef": row.public_ref, "role": row.role, "modality": row.modality,
                   "content": row.content, "purged": row.purged_at is not None, "createdAt": row.created_at} for row in turns]}


def purge_preview(db: Session, days: int) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    base = (TutorTurn.created_at < cutoff, TutorTurn.purged_at.is_(None))
    return {"olderThanDays": days, "cutoff": cutoff,
        "turnCount": db.scalar(select(func.count()).select_from(TutorTurn).where(*base)) or 0,
        "sessionCount": db.scalar(select(func.count(func.distinct(TutorTurn.session_id))).where(*base)) or 0}


def purge(db: Session, principal: Principal, days: int, reason: str) -> dict:
    preview = purge_preview(db, days); now = datetime.now(timezone.utc)
    result = db.execute(update(TutorTurn).where(TutorTurn.created_at < preview["cutoff"], TutorTurn.purged_at.is_(None)).values(
        content="[Transcript content purged by an administrator.]", response_data={}, purged_at=now))
    db.add(AuditEvent(actor_id=principal.user.id, action="tutor_transcript.purged", target_type="tutor_turn",
        target_id=f"before:{preview['cutoff'].isoformat()}", event_data={"reason": reason, "turnCount": result.rowcount, "olderThanDays": days}))
    db.commit(); return {**preview, "purgedTurnCount": result.rowcount}
