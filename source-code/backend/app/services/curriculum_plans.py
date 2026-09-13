import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import (
    AssessmentCurriculumSnapshot, AuditEvent, CurriculumPlan, CurriculumPlanUnit, Document,
    Question, QuestionUnit, StudentProgression, StudentSubject, TextbookContentVersion, TextbookUnit,
)
from app.schemas.curriculum_plans import (
    CoverageDiagnosticResponse, CurriculumPlanResponse, PlanPeriod, PlanUnitResponse,
    QuestionPoolDiagnosticResponse, SavePlanRequest,
)
from app.security import Principal


def _published_textbook(db: Session, subject_id: str):
    row = db.execute(select(TextbookContentVersion, Document).join(
        Document, Document.id == TextbookContentVersion.document_id
    ).where(
        TextbookContentVersion.course_id == "igcse", TextbookContentVersion.subject_id == subject_id,
        TextbookContentVersion.status == "published", Document.removed_at.is_(None),
    ).order_by(TextbookContentVersion.published_at.desc())).first()
    if not row:
        raise DomainError("published_textbook_required", "Publish a textbook for this subject first.", 409)
    return row


def _current_plan(db: Session, subject_id: str):
    return db.scalar(select(CurriculumPlan).where(
        CurriculumPlan.course_id == "igcse", CurriculumPlan.subject_id == subject_id,
        CurriculumPlan.status.in_(("draft", "published")),
    ).order_by(CurriculumPlan.version_number.desc()))


def _units(db: Session, content_version_id):
    return db.scalars(select(TextbookUnit).where(
        TextbookUnit.content_version_id == content_version_id
    ).order_by(TextbookUnit.sequence)).all()


def _response(db: Session, plan: CurriculumPlan, document: Document) -> CurriculumPlanResponse:
    units = _units(db, plan.textbook_content_version_id)
    rows = db.scalars(select(CurriculumPlanUnit).where(CurriculumPlanUnit.plan_id == plan.id)).all()
    periods = []
    for grade in (10, 11):
        for term in (1, 2, 3):
            periods.append(PlanPeriod(
                grade=grade, term=term,
                unitIds=[str(row.unit_id) for row in rows if row.grade == grade and row.term == term],
            ))
    return CurriculumPlanResponse(
        versionNumber=plan.version_number, status=plan.status, subjectId=plan.subject_id,
        textbookTitle=document.title, textbookEdition=document.edition or "",
        availableUnits=[PlanUnitResponse(id=str(unit.id), code=unit.unit_code, title=unit.title) for unit in units],
        periods=periods,
    )


def get_plan(db: Session, subject_id: str) -> CurriculumPlanResponse:
    content, document = _published_textbook(db, subject_id)
    plan = _current_plan(db, subject_id)
    if not plan:
        units = _units(db, content.id)
        return CurriculumPlanResponse(
            versionNumber=0, status="not_started", subjectId=subject_id,
            textbookTitle=document.title, textbookEdition=document.edition or "",
            availableUnits=[PlanUnitResponse(id=str(unit.id), code=unit.unit_code, title=unit.title) for unit in units],
            periods=[PlanPeriod(grade=grade, term=term) for grade in (10, 11) for term in (1, 2, 3)],
        )
    return _response(db, plan, document)


def save_plan(db: Session, principal: Principal, subject_id: str, payload: SavePlanRequest):
    content, document = _published_textbook(db, subject_id)
    plan = _current_plan(db, subject_id)
    if plan and plan.status == "published":
        plan = None
    if not plan:
        next_version = (db.scalar(select(func.max(CurriculumPlan.version_number)).where(
            CurriculumPlan.course_id == "igcse", CurriculumPlan.subject_id == subject_id
        )) or 0) + 1
        plan = CurriculumPlan(
            course_id="igcse", subject_id=subject_id, textbook_content_version_id=content.id,
            version_number=next_version, status="draft", created_by=principal.user.id,
        )
        db.add(plan); db.flush()
    allowed = {str(unit.id) for unit in _units(db, content.id)}
    periods = {(row.grade, row.term) for row in payload.periods}
    if len(periods) != len(payload.periods):
        raise DomainError("duplicate_curriculum_period", "Each Grade and Term may appear only once.", 409)
    selected = [unit_id for period in payload.periods for unit_id in period.unitIds]
    if any(unit_id not in allowed for unit_id in selected):
        raise DomainError("invalid_curriculum_unit", "Coverage may use only units from this published subject textbook.", 422)
    if len(selected) != len(set(selected)):
        raise DomainError("duplicate_curriculum_unit", "A unit may be introduced in only one Grade and Term.", 409)
    db.execute(delete(CurriculumPlanUnit).where(CurriculumPlanUnit.plan_id == plan.id))
    for period in payload.periods:
        for unit_id in period.unitIds:
            db.add(CurriculumPlanUnit(plan_id=plan.id, grade=period.grade, term=period.term, unit_id=uuid.UUID(unit_id)))
    db.add(AuditEvent(actor_id=principal.user.id, action="curriculum_plan.saved", target_type="curriculum_plan", target_id=str(plan.id), event_data={"subjectId": subject_id, "versionNumber": plan.version_number}))
    db.commit(); db.refresh(plan)
    return _response(db, plan, document)


def publish_plan(db: Session, principal: Principal, subject_id: str, confirmation):
    content, document = _published_textbook(db, subject_id)
    plan = _current_plan(db, subject_id)
    if not plan or plan.status != "draft":
        raise DomainError("curriculum_draft_required", "Save a curriculum-plan draft first.", 409)
    if not confirmation.confirmSubject or not confirmation.confirmTextbook:
        raise DomainError("curriculum_confirmation_required", "Confirm subject and textbook before publishing.", 422)
    if plan.textbook_content_version_id != content.id:
        raise DomainError("curriculum_textbook_superseded", "Rebuild the plan using the currently published textbook.", 409)
    rows = db.scalars(select(CurriculumPlanUnit).where(CurriculumPlanUnit.plan_id == plan.id)).all()
    if not rows:
        raise DomainError("curriculum_units_required", "Assign at least one unit before publishing.", 409)
    now = datetime.now(timezone.utc)
    for old in db.scalars(select(CurriculumPlan).where(
        CurriculumPlan.course_id == "igcse", CurriculumPlan.subject_id == subject_id,
        CurriculumPlan.status == "published",
    ).with_for_update()).all():
        old.status = "superseded"; old.superseded_at = now
    plan.status = "published"; plan.published_by = principal.user.id; plan.published_at = now
    db.add(AuditEvent(actor_id=principal.user.id, action="curriculum_plan.published", target_type="curriculum_plan", target_id=str(plan.id), event_data={"subjectId": subject_id, "versionNumber": plan.version_number}))
    db.commit(); db.refresh(plan)
    return _response(db, plan, document)


def student_coverage(db: Session, student_id: uuid.UUID, subject_id: str) -> CoverageDiagnosticResponse:
    if not db.get(StudentSubject, {"student_id": student_id, "subject_id": subject_id}):
        raise DomainError("student_subject_not_enrolled", "The student is not enrolled in this subject.", 409)
    progress = db.scalars(select(StudentProgression).where(
        StudentProgression.student_id == student_id, StudentProgression.course_id == "igcse"
    ).order_by(StudentProgression.grade, StudentProgression.term)).all()
    current = next((row for row in progress if row.is_current), None)
    if not current:
        return CoverageDiagnosticResponse(status="missing_progression", message="Configure the student's current Grade and Term.")
    plan = db.scalar(select(CurriculumPlan).where(
        CurriculumPlan.course_id == "igcse", CurriculumPlan.subject_id == subject_id,
        CurriculumPlan.status == "published",
    ).order_by(CurriculumPlan.version_number.desc()))
    if not plan:
        return CoverageDiagnosticResponse(status="missing_plan", message="Publish curriculum coverage for this subject.", currentGrade=current.grade, currentTerm=current.term)
    reached = {(row.grade, row.term) for row in progress if (row.grade, row.term) <= (current.grade, current.term)}
    rows = db.scalars(select(CurriculumPlanUnit).where(CurriculumPlanUnit.plan_id == plan.id)).all()
    missing = [f"Grade {grade} Term {term}" for grade, term in sorted(reached) if not any(row.grade == grade and row.term == term for row in rows)]
    if missing:
        return CoverageDiagnosticResponse(status="missing_coverage", message="Coverage is missing for part of the student's progression.", planVersion=plan.version_number, currentGrade=current.grade, currentTerm=current.term, missingPeriods=missing)
    ids = {row.unit_id for row in rows if (row.grade, row.term) in reached}
    units = db.scalars(select(TextbookUnit).where(TextbookUnit.id.in_(ids)).order_by(TextbookUnit.sequence)).all() if ids else []
    return CoverageDiagnosticResponse(status="ready", message="Cumulative coverage is ready.", planVersion=plan.version_number, currentGrade=current.grade, currentTerm=current.term, coveredUnits=[PlanUnitResponse(id=str(unit.id), code=unit.unit_code, title=unit.title) for unit in units])


def snapshot(db: Session, assessment_ref: str, student_id: uuid.UUID, subject_id: str):
    existing = db.scalar(select(AssessmentCurriculumSnapshot).where(AssessmentCurriculumSnapshot.assessment_ref == assessment_ref))
    if existing:
        return existing
    coverage = student_coverage(db, student_id, subject_id)
    if coverage.status != "ready":
        raise DomainError("assessment_coverage_not_ready", coverage.message, 409, [{"missingPeriods": coverage.missingPeriods}])
    plan = db.scalar(select(CurriculumPlan).where(CurriculumPlan.subject_id == subject_id, CurriculumPlan.status == "published"))
    progress = db.scalars(select(StudentProgression).where(StudentProgression.student_id == student_id).order_by(StudentProgression.grade, StudentProgression.term)).all()
    current = next(row for row in progress if row.is_current)
    row = AssessmentCurriculumSnapshot(
        assessment_ref=assessment_ref, student_id=student_id, plan_id=plan.id,
        course_id="igcse", subject_id=subject_id, grade=current.grade, term=current.term,
        covered_unit_ids=[unit.id for unit in coverage.coveredUnits],
        progression_periods=[{"grade": p.grade, "term": p.term} for p in progress if (p.grade, p.term) <= (current.grade, current.term)],
    )
    db.add(row); db.commit(); db.refresh(row)
    return row


def question_pool_diagnostic(
    db: Session, student_id: uuid.UUID, subject_id: str,
    requested_question_count: int = 0, requested_marks: int = 0,
) -> QuestionPoolDiagnosticResponse:
    coverage = student_coverage(db, student_id, subject_id)
    if coverage.status != "ready":
        return QuestionPoolDiagnosticResponse(
            status=coverage.status, message=coverage.message, planVersion=coverage.planVersion,
            requestedQuestionCount=requested_question_count, requestedMarks=requested_marks,
            shortageQuestionCount=requested_question_count, shortageMarks=requested_marks,
        )
    covered = {uuid.UUID(unit.id) for unit in coverage.coveredUnits}
    questions = db.scalars(select(Question).where(
        Question.course_id == "igcse", Question.subject_id == subject_id,
        Question.review_state == "published",
    )).all()
    eligible = []
    for question in questions:
        mappings = set(db.scalars(select(QuestionUnit.unit_id).where(
            QuestionUnit.question_id == question.id
        )).all())
        if mappings and mappings.issubset(covered):
            eligible.append(question)
    count = len(eligible)
    marks = sum(question.marks for question in eligible)
    shortage_count = max(0, requested_question_count - count)
    shortage_marks = max(0, requested_marks - marks)
    ready = shortage_count == 0 and shortage_marks == 0
    return QuestionPoolDiagnosticResponse(
        status="ready" if ready else "question_pool_shortage",
        message="The eligible question pool is ready." if ready else "The eligible question pool is too small for this assessment.",
        planVersion=coverage.planVersion, eligibleQuestionCount=count, eligibleMarks=marks,
        requestedQuestionCount=requested_question_count, requestedMarks=requested_marks,
        shortageQuestionCount=shortage_count, shortageMarks=shortage_marks,
    )
