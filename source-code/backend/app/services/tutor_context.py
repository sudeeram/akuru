import hashlib
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import DomainError
from app.models import (
    Assessment, AssessmentQuestion, AssessmentResult, ImprovementRecommendation, StudyPlan,
    StudyPlanItem, TextbookUnit, TutorLearnerContextLog, TutorSession, UnitMastery,
    UnitMasteryDimension, UnitMasteryEvent, WeaknessDiagnosis,
)
from app.schemas.curriculum_plans import PlanUnitResponse
from app.schemas.tutor_context import (
    ContextAttempt, ContextEvidence, ContextMistakePattern, ContextPlanItem,
    ContextReviewedRecommendation, ContextStatement, ContextUnit, LearnerContextResponse,
    ProviderLearnerContext,
)
from app.security import Principal
from app.services import curriculum_plans, tutor_sessions
from app.services.assessment_access import TutorCapability, require_tutor_access


CONTEXT_ALGORITHM = "learner-context-v1"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _reference(kind: str, row_id: uuid.UUID, version: int | None = None) -> str:
    suffix = f":v{version}" if version is not None else ""
    return f"{kind}:{row_id}{suffix}"


def _topic(row: WeaknessDiagnosis) -> str:
    explicit = row.evidence.get("topic") if isinstance(row.evidence, dict) else None
    if isinstance(explicit, str) and explicit.strip():
        return " ".join(explicit.split())[:120]
    return row.category.replace("_", " ")


def _signal_statements(unit: TextbookUnit, mastery: UnitMastery | None, events: list[UnitMasteryEvent]):
    refs = [_reference("mastery", event.id) for event in events]
    label = f"{unit.unit_code} – {unit.title}"
    if not mastery or not events:
        return ["insufficient_evidence"], [ContextStatement(
            text=f"I do not yet have assessed evidence about your skills in {label}.",
            signal="insufficient_evidence", evidenceRefs=[], cautious=True,
        )]
    sparse = len(events) < 2 or mastery.variety_count < 2
    last_evidence = getattr(mastery, "last_evidence_at", None)
    stale = bool(last_evidence and last_evidence < _now() - timedelta(days=90))
    low = mastery.confidence == "low" or mastery.provisional or sparse or stale
    if low:
        reason = "old or limited" if stale else "still limited"
        return ["low_confidence"], [ContextStatement(
            text=f"Assessed evidence for {label} is {reason}, so we should gather more evidence before judging this unit.",
            signal="low_confidence", evidenceRefs=refs, cautious=True,
        )]
    signals, statements = [], []
    score = float(mastery.display_score)
    if score >= 7:
        signals.append("strong")
        statements.append(ContextStatement(text=f"Your assessed work shows strong skills in {label}.", signal="strong", evidenceRefs=refs, cautious=False))
    elif score <= 4:
        signals.append("weak")
        statements.append(ContextStatement(text=f"Your assessed work shows that {label} needs more practice.", signal="weak", evidenceRefs=refs, cautious=False))
    if float(mastery.trend) >= 0.35:
        signals.append("improving")
        statements.append(ContextStatement(text=f"Your recent assessed results in {label} are improving.", signal="improving", evidenceRefs=refs, cautious=False))
    elif float(mastery.trend) <= -0.35:
        signals.append("declining")
        statements.append(ContextStatement(text=f"Your recent assessed results in {label} are declining, so a review may help.", signal="declining", evidenceRefs=refs, cautious=False))
    if not signals:
        signals.append("assessed")
    return signals, statements


def _valid_mastery_events(db: Session, student_id: uuid.UUID, unit_id: uuid.UUID) -> list[UnitMasteryEvent]:
    rows = db.execute(select(UnitMasteryEvent, AssessmentQuestion).join(
        AssessmentResult, AssessmentResult.id == UnitMasteryEvent.trigger_result_id
    ).join(AssessmentQuestion, AssessmentQuestion.id == AssessmentResult.question_id
    ).where(
        UnitMasteryEvent.student_id == student_id, UnitMasteryEvent.unit_id == unit_id,
        AssessmentResult.status == "published",
    ).order_by(UnitMasteryEvent.created_at)).all()
    return [event for event, question in rows if str(unit_id) in question.unit_ids]


def _attempts(db: Session, student_id: uuid.UUID, subject_id: str, unit_id: uuid.UUID):
    rows = db.execute(select(AssessmentResult, AssessmentQuestion, Assessment).join(
        AssessmentQuestion, AssessmentQuestion.id == AssessmentResult.question_id
    ).join(Assessment, Assessment.id == AssessmentResult.assessment_id).where(
        Assessment.student_id == student_id, Assessment.subject_id == subject_id,
        AssessmentResult.status == "published",
    ).order_by(AssessmentResult.created_at.desc(), AssessmentResult.version_number.desc())).all()
    seen, attempts, evidence = set(), [], []
    for result, question, assessment in rows:
        if str(unit_id) not in question.unit_ids or question.id in seen:
            continue
        seen.add(question.id)
        ref = _reference("assessment", result.id, result.version_number)
        missing = [str(item.get("rationale", ""))[:240] for item in result.marking_decisions if not item.get("awarded")]
        attempts.append(ContextAttempt(evidenceRef=ref, observedAt=result.created_at, mode=assessment.mode,
            score=round(result.awarded_marks / result.max_marks * 10, 1), awardedMarks=result.awarded_marks,
            maxMarks=result.max_marks, markingSummary=missing[:8]))
        evidence.append(ContextEvidence(ref=ref, kind="assessment_result", observedAt=result.created_at,
            summary=f"Assessed {result.awarded_marks}/{result.max_marks}; {len(missing)} marking points were not awarded."))
    return attempts[:10], evidence[:10]


def _mistakes(db: Session, student_id: uuid.UUID, subject_id: str, unit_id: uuid.UUID, now: datetime):
    rows = db.scalars(select(WeaknessDiagnosis).join(
        AssessmentResult, AssessmentResult.id == WeaknessDiagnosis.result_id
    ).where(
        WeaknessDiagnosis.student_id == student_id, WeaknessDiagnosis.subject_id == subject_id,
        WeaknessDiagnosis.unit_id == unit_id, AssessmentResult.status == "published",
    ).order_by(WeaknessDiagnosis.created_at)).all()
    grouped = defaultdict(list)
    for row in rows:
        grouped[(_topic(row), row.category)].append(row)
    patterns, evidence = [], []
    for (topic, category), items in sorted(grouped.items()):
        refs = [_reference("mistake", item.id) for item in items]
        seven = sum(item.created_at >= now - timedelta(days=7) for item in items)
        thirty = sum(item.created_at >= now - timedelta(days=30) for item in items)
        recent_phrase = f"{seven} times in the last 7 days" if seven else f"{thirty} times in the last 30 days" if thirty else f"{len(items)} times in retained assessed work"
        statement = ContextStatement(
            text=f"AKURU found assessed mistakes about {topic} {recent_phrase}.", signal="recurring_mistake",
            evidenceRefs=refs, cautious=any(item.confidence < .75 for item in items),
        )
        patterns.append(ContextMistakePattern(topic=topic, category=category, last7Days=seven,
            last30Days=thirty, lifetime=len(items), evidenceRefs=refs, statement=statement))
        for item, ref in zip(items, refs):
            evidence.append(ContextEvidence(ref=ref, kind="mistake", observedAt=item.created_at,
                summary=f"Assessed {item.severity} {category.replace('_', ' ')} evidence about {topic}."))
    return patterns, evidence


def _plan_items(db: Session, student_id: uuid.UUID, subject_id: str, unit_id: uuid.UUID):
    rows = db.execute(select(StudyPlanItem, ImprovementRecommendation).join(
        StudyPlan, StudyPlan.id == StudyPlanItem.plan_id
    ).join(ImprovementRecommendation, ImprovementRecommendation.id == StudyPlanItem.recommendation_id).where(
        StudyPlan.student_id == student_id, StudyPlan.status == "active",
        StudyPlanItem.student_id == student_id, StudyPlanItem.subject_id == subject_id,
        StudyPlanItem.unit_id == unit_id, ImprovementRecommendation.review_status == "approved",
    ).order_by(StudyPlanItem.sequence)).all()
    items, evidence = [], []
    for item, _ in rows:
        ref = _reference("plan", item.id)
        items.append(ContextPlanItem(evidenceRef=ref, title=item.title, activityType=item.activity_type,
            status=item.status, scheduledFor=item.scheduled_for))
        evidence.append(ContextEvidence(ref=ref, kind="study_plan_item", observedAt=item.created_at,
            summary=f"Approved {item.activity_type.replace('_', ' ')} activity: {item.title}."))
    return items, evidence


def _reviewed_recommendations(db: Session, student_id: uuid.UUID, subject_id: str, unit_id: uuid.UUID):
    rows = db.scalars(select(ImprovementRecommendation).where(
        ImprovementRecommendation.student_id == student_id,
        ImprovementRecommendation.subject_id == subject_id,
        ImprovementRecommendation.unit_id == unit_id,
        ImprovementRecommendation.review_status == "approved",
    ).order_by(ImprovementRecommendation.created_at, ImprovementRecommendation.id)).all()
    items, evidence = [], []
    for row in rows:
        ref = _reference("recommendation", row.id)
        items.append(ContextReviewedRecommendation(evidenceRef=ref, title=row.title,
            activityType=row.activity_type, reason=row.reason, action=row.action,
            successCondition=row.success_condition))
        evidence.append(ContextEvidence(ref=ref, kind="reviewed_recommendation", observedAt=row.created_at,
            summary=f"Reviewed {row.activity_type.replace('_', ' ')} recommendation: {row.title}."))
    return items, evidence


def _build(db: Session, student_id: uuid.UUID, session: TutorSession, operation_ref: str, generated_at: datetime):
    coverage = curriculum_plans.student_coverage(db, student_id, session.subject_id)
    if coverage.status != "ready":
        raise DomainError("tutor_coverage_not_ready", coverage.message, 409)
    covered_ids = {item.id for item in coverage.coveredUnits}
    if str(session.active_unit_id) not in covered_ids:
        raise DomainError("tutor_unit_not_eligible", "The active tutor unit is no longer eligible.", 409)
    units, all_evidence = [], []
    for covered in coverage.coveredUnits:
        unit_id = uuid.UUID(covered.id)
        unit = db.get(TextbookUnit, unit_id)
        mastery = db.scalar(select(UnitMastery).where(UnitMastery.student_id == student_id, UnitMastery.unit_id == unit_id))
        events = _valid_mastery_events(db, student_id, unit_id)
        statements_signals, statements = _signal_statements(unit, mastery, events)
        for event in events:
            all_evidence.append(ContextEvidence(ref=_reference("mastery", event.id), kind="mastery_event",
                observedAt=event.created_at, summary=f"Mastery changed to {float(event.new_score):.1f}/10 from a published assessment result."))
        attempts, attempt_evidence = _attempts(db, student_id, session.subject_id, unit_id)
        mistakes, mistake_evidence = _mistakes(db, student_id, session.subject_id, unit_id, generated_at)
        recommendations, recommendation_evidence = _reviewed_recommendations(db, student_id, session.subject_id, unit_id)
        plans, plan_evidence = _plan_items(db, student_id, session.subject_id, unit_id)
        for pattern in mistakes:
            statements.append(pattern.statement)
            statements_signals.append("recurring_mistake")
        for item in plans:
            statements.append(ContextStatement(text=f"Your current study plan includes {item.title} for {unit.unit_code}.",
                signal="planned_activity", evidenceRefs=[item.evidenceRef], cautious=False))
        dimensions = {}
        if mastery and events:
            dimensions = {row.dimension: float(row.score) for row in db.scalars(select(UnitMasteryDimension).where(UnitMasteryDimension.mastery_id == mastery.id)).all()}
        units.append(ContextUnit(unit=PlanUnitResponse(id=str(unit.id), code=unit.unit_code, title=unit.title),
            active=unit.id == session.active_unit_id, masteryScore=float(mastery.display_score) if mastery and events else None,
            confidence=mastery.confidence if mastery and events else None, trend=float(mastery.trend) if mastery and events else None,
            evidenceCount=len(events), varietyCount=mastery.variety_count if mastery and events else 0,
            dimensions=dimensions, signals=list(dict.fromkeys(statements_signals)), statements=statements,
            attempts=attempts, mistakes=mistakes, reviewedRecommendations=recommendations, studyPlan=plans))
        all_evidence.extend(attempt_evidence + mistake_evidence + recommendation_evidence + plan_evidence)
    evidence_by_ref = {item.ref: item for item in all_evidence}
    all_evidence = [evidence_by_ref[key] for key in sorted(evidence_by_ref)]
    digest_input = "|".join([CONTEXT_ALGORITHM, generated_at.date().isoformat(), session.subject_id,
                             str(session.active_unit_id)] + [item.ref for item in all_evidence])
    context_version = hashlib.sha256(digest_input.encode()).hexdigest()
    active_unit = next(item.unit for item in units if item.active)
    provider = ProviderLearnerContext(
        learnerRef="learner_" + hashlib.sha256(f"akuru:{student_id}".encode()).hexdigest()[:20],
        subjectId=session.subject_id, activeUnitCode=active_unit.code, contextVersion=context_version,
        learningSignals=[{"unitCode": unit.unit.code, "signals": unit.signals,
                          "statements": [statement.model_dump(mode="json") for statement in unit.statements]}
                         for unit in units],
        recurringMistakes=[{"unitCode": unit.unit.code, "topic": pattern.topic,
                            "last7Days": pattern.last7Days, "last30Days": pattern.last30Days,
                            "evidenceRefs": pattern.evidenceRefs}
                           for unit in units for pattern in unit.mistakes],
        reviewedRecommendations=[{"unitCode": unit.unit.code, "title": item.title,
                                  "activityType": item.activityType, "evidenceRef": item.evidenceRef}
                                 for unit in units for item in unit.reviewedRecommendations],
        plannedActivities=[{"unitCode": unit.unit.code, "title": item.title,
                            "activityType": item.activityType, "evidenceRef": item.evidenceRef}
                           for unit in units for item in unit.studyPlan],
    )
    return LearnerContextResponse(operationRef=operation_ref, contextVersion=context_version,
        generatedAt=generated_at, subjectId=session.subject_id, activeUnit=active_unit,
        units=units, evidence=all_evidence, providerContext=provider)


def build_and_log(db: Session, settings: Settings, principal: Principal, session_ref: str, request_key: str):
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TEXT)
    session = tutor_sessions._owned_session(db, principal.user.id, session_ref, lock=True)
    if session.status != "active":
        raise DomainError("tutor_session_ended", "This tutor session has ended.", 409)
    existing = db.scalar(select(TutorLearnerContextLog).where(
        TutorLearnerContextLog.session_id == session.id, TutorLearnerContextLog.request_key == request_key))
    if existing:
        return LearnerContextResponse.model_validate(existing.context_snapshot)
    operation_ref = f"tutor_context_{uuid.uuid4().hex}"
    payload = _build(db, principal.user.id, session, operation_ref, _now())
    log = TutorLearnerContextLog(public_ref=operation_ref, session_id=session.id, student_id=principal.user.id,
        subject_id=session.subject_id, active_unit_id=session.active_unit_id, request_key=request_key,
        context_version=payload.contextVersion, evidence_references=[item.ref for item in payload.evidence],
        context_snapshot=payload.model_dump(mode="json"))
    db.add(log); db.commit()
    return payload
