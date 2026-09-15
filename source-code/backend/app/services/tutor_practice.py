import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import DomainError
from app.models import (
    AssessmentInteraction, AssessmentQuestion, StudentProfile, TextbookUnit, TutorPractice,
    TutorSession, TutorSignal, User,
)
from app.schemas.assessments import AnswerSave, AssessmentMode
from app.schemas.tutor_practice import TutorPracticeResponse, TutorSignalListResponse, TutorSignalResponse
from app.security import Principal
from app.services import assessment_marking, assessments, tutor_sessions
from app.services.assessment_access import TutorCapability, require_tutor_access


def _active(db: Session, student_id: uuid.UUID, session_ref: str, *, required: bool = True):
    session = tutor_sessions._owned_session(db, student_id, session_ref)
    tutor_sessions._require_active(session)
    row = db.scalar(select(TutorPractice).where(
        TutorPractice.session_id == session.id, TutorPractice.status == "active"))
    if required and not row:
        raise DomainError("tutor_practice_not_found", "Start guided practice first.", 404)
    return session, row


def _response(db: Session, row: TutorPractice, latest_hint: str | None = None) -> TutorPracticeResponse:
    unit = db.get(TextbookUnit, row.unit_id)
    assessment = assessments._owned(db, SimpleNamespace(user=SimpleNamespace(id=row.student_id)), row.assessment_id)
    payload = assessments.response(db, assessment)
    question = next(item for item in payload.questions if item.id == row.question_id)
    feedback_visible = bool(payload.feedbackVisible and question.result and question.result.status == "published")
    if question.result and question.result.status != "published":
        question = question.model_copy(update={"result": None})
    hints = db.scalar(select(func.count()).select_from(AssessmentInteraction).where(
        AssessmentInteraction.assessment_id == row.assessment_id,
        AssessmentInteraction.question_id == row.question_id, AssessmentInteraction.kind == "hint")) or 0
    return TutorPracticeResponse(practiceRef=row.public_ref, status=row.status, unitCode=unit.unit_code,
        unitTitle=unit.title, question=question,
        assetUrls=[f"/api/v1/assessments/{row.assessment_id}/assets/{asset_id}" for asset_id in question.assetIds],
        hintCount=hints, latestHint=latest_hint,
        feedbackVisible=feedback_visible, createdAt=row.created_at, submittedAt=row.submitted_at)


def current(db: Session, settings: Settings, principal: Principal, session_ref: str):
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TEXT)
    session = tutor_sessions._owned_session(db, principal.user.id, session_ref)
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS,
                         session.subject_id, "tutor_practice")
    row = db.scalar(select(TutorPractice).where(TutorPractice.session_id == session.id)
                    .order_by(TutorPractice.created_at.desc()))
    return _response(db, row) if row else None


def start(db: Session, settings: Settings, principal: Principal, session_ref: str, request_key: str):
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TEXT)
    session, active = _active(db, principal.user.id, session_ref, required=False)
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS,
                         session.subject_id, "tutor_practice")
    replay = db.scalar(select(TutorPractice).where(
        TutorPractice.session_id == session.id, TutorPractice.request_key == request_key))
    if replay:
        return _response(db, replay)
    if active:
        return _response(db, active)
    assessment = assessments.start(db, principal, SimpleNamespace(
        mode=AssessmentMode.PRACTICE, subjectId=session.subject_id, blueprintId=None, paperId=None),
        required_unit_id=session.active_unit_id)
    question = assessment.questions[0]
    row = TutorPractice(public_ref=f"tutor_practice_{uuid.uuid4().hex}", session_id=session.id,
        student_id=principal.user.id, subject_id=session.subject_id, unit_id=session.active_unit_id,
        assessment_id=assessment.id, question_id=question.id, request_key=request_key)
    db.add(row); db.commit(); db.refresh(row)
    return _response(db, row)


def hint(db: Session, settings: Settings, principal: Principal, session_ref: str, request_key: str):
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TEXT)
    session, row = _active(db, principal.user.id, session_ref)
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS,
                         session.subject_id, "tutor_practice")
    value = assessments.record_hint(db, principal, row.assessment_id, row.question_id, request_key)
    return _response(db, row, value["hint"])


def answer(db: Session, settings: Settings, principal: Principal, session_ref: str, text: str, request_key: str):
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TEXT)
    session, row = _active(db, principal.user.id, session_ref)
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS,
                         session.subject_id, "tutor_practice")
    assessments.save_answer(db, principal, row.assessment_id,
        AnswerSave(questionId=row.question_id, answer=text, idempotencyKey=request_key))
    return _response(db, row)


def submit(db: Session, settings: Settings, principal: Principal, session_ref: str, request_key: str):
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TEXT)
    session, row = _active(db, principal.user.id, session_ref)
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS,
                         session.subject_id, "tutor_practice")
    assessment = assessments.submit(db, principal, row.assessment_id, request_key)
    assessment_marking.evaluate(db, settings, assessments._owned(db, principal, assessment.id, True), request_key)
    row.status = "submitted"; row.submitted_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(row)
    return _response(db, row)


def signal_response(db: Session, row: TutorSignal) -> TutorSignalResponse:
    unit = db.get(TextbookUnit, row.unit_id); student = db.get(User, row.student_id)
    session = db.get(TutorSession, row.session_id)
    return TutorSignalResponse(signalRef=row.public_ref, studentName=student.display_name,
        subjectId=session.subject_id, unitCode=unit.unit_code, unitTitle=unit.title,
        category=row.category, observation=row.observation, confidence=row.confidence,
        evidenceCount=len(row.evidence_references), promptName=row.prompt_name,
        promptVersion=row.prompt_version, createdAt=row.created_at)


def list_signals(db: Session, principal: Principal, student_id: uuid.UUID | None = None):
    target = principal.user.id if principal.user.role == "student" else student_id
    if not target:
        raise DomainError("student_required", "Choose a child.", 422)
    if principal.user.role == "parent":
        linked = db.scalar(select(StudentProfile).where(
            StudentProfile.student_id == target, StudentProfile.parent_id == principal.user.id))
        if not linked:
            raise DomainError("student_not_found", "Student not found.", 404)
    elif principal.user.role != "admin" and target != principal.user.id:
        raise DomainError("student_not_found", "Student not found.", 404)
    rows = db.scalars(select(TutorSignal).where(TutorSignal.student_id == target)
                      .order_by(TutorSignal.created_at.desc()).limit(100)).all()
    return TutorSignalListResponse(signals=[signal_response(db, row) for row in rows])
