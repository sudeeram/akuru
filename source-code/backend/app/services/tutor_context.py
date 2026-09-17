import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import DomainError
from app.models import (
    Assessment, AssessmentQuestion, AssessmentResult, ImprovementRecommendation, StudyPlan,
    StudyPlanItem, TextbookGroup, TextbookTopic, TopicMastery, TopicMasteryDimension,
    TopicMasteryEvent, TutorLearnerContextLog, TutorSession, WeaknessDiagnosis,
)
from app.schemas.curriculum_plans import PlanTopicResponse
from app.schemas.tutor_context import (
    ContextAttempt, ContextEvidence, ContextMistakePattern, ContextPlanItem,
    ContextReviewedRecommendation, ContextStatement, ContextTopic, LearnerContextResponse,
    ProviderLearnerContext,
)
from app.security import Principal
from app.services import curriculum_plans, tutor_sessions
from app.services.assessment_access import TutorCapability, require_tutor_access

CONTEXT_ALGORITHM = "learner-context-v2-topics"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _reference(kind: str, row_id: uuid.UUID, version: int | None = None) -> str:
    suffix = f":v{version}" if version is not None else ""
    return f"{kind}:{row_id}{suffix}"


def _reviewed_recommendations(db: Session, student_id: uuid.UUID, subject_id: str, topic_id: uuid.UUID):
    rows = db.scalars(select(ImprovementRecommendation).where(
        ImprovementRecommendation.student_id == student_id,
        ImprovementRecommendation.subject_id == subject_id,
        ImprovementRecommendation.topic_id == topic_id,
        ImprovementRecommendation.review_status == "approved",
    ).order_by(ImprovementRecommendation.created_at)).all()
    return (
        [ContextReviewedRecommendation(evidenceRef=_reference("recommendation", row.id), title=row.title,
            activityType=row.activity_type, reason=row.reason, action=row.action,
            successCondition=row.success_condition) for row in rows],
        [ContextEvidence(ref=_reference("recommendation", row.id), kind="reviewed_recommendation",
            observedAt=row.created_at, summary=row.title) for row in rows],
    )


def _plan_items(db: Session, student_id: uuid.UUID, subject_id: str, topic_id: uuid.UUID):
    rows = db.scalars(select(StudyPlanItem).join(StudyPlan, StudyPlan.id == StudyPlanItem.plan_id).where(
        StudyPlan.student_id == student_id, StudyPlan.status == "active",
        StudyPlanItem.subject_id == subject_id, StudyPlanItem.topic_id == topic_id,
    ).order_by(StudyPlanItem.sequence)).all()
    return (
        [ContextPlanItem(evidenceRef=_reference("plan", row.id), title=row.title,
            activityType=row.activity_type, status=row.status, scheduledFor=row.scheduled_for) for row in rows],
        [ContextEvidence(ref=_reference("plan", row.id), kind="study_plan_item",
            observedAt=row.created_at, summary=row.title) for row in rows],
    )


def _build(db: Session, student_id: uuid.UUID, session: TutorSession,
           operation_ref: str, generated_at: datetime) -> LearnerContextResponse:
    coverage = curriculum_plans.student_coverage(db, student_id, session.subject_id)
    refs = {row.topicRef for row in coverage.coveredTopics} if coverage.status == "ready" else set()
    active = db.get(TextbookTopic, session.active_topic_id)
    if not active or active.public_ref not in refs:
        raise DomainError("tutor_topic_not_eligible", "The active Tutor topic is no longer covered.", 409)
    rows = db.execute(select(TextbookTopic, TextbookGroup).join(
        TextbookGroup, TextbookGroup.id == TextbookTopic.group_id
    ).where(TextbookTopic.public_ref.in_(refs)).order_by(
        TextbookGroup.sequence, TextbookTopic.sequence)).all()
    topics: list[ContextTopic] = []
    evidence: list[ContextEvidence] = []
    for topic, group in rows:
        mastery = db.scalar(select(TopicMastery).where(
            TopicMastery.student_id == student_id, TopicMastery.topic_id == topic.id))
        events = db.scalars(select(TopicMasteryEvent).join(
            AssessmentResult, AssessmentResult.id == TopicMasteryEvent.trigger_result_id
        ).where(TopicMasteryEvent.student_id == student_id, TopicMasteryEvent.topic_id == topic.id,
                AssessmentResult.status == "published").order_by(TopicMasteryEvent.created_at)).all()
        label = f"{group.code} · {topic.code} – {topic.title}"
        if not mastery or not events:
            signals = ["insufficient_evidence"]
            statements = [ContextStatement(text=f"I do not yet have assessed evidence about {label}.",
                signal="insufficient_evidence", evidenceRefs=[], cautious=True)]
        else:
            score = float(mastery.display_score)
            event_refs = [_reference("topic_mastery", event.id) for event in events]
            if mastery.confidence == "low" or mastery.provisional:
                signal = "low_confidence"
            elif score >= 7:
                signal = "strong"
            elif score <= 4:
                signal = "weak"
            elif float(mastery.trend) >= .35:
                signal = "improving"
            elif float(mastery.trend) <= -.35:
                signal = "declining"
            else:
                signal = "low_confidence"
            signals = [signal]
            statements = [ContextStatement(text=f"Your assessed topic mastery for {label} is {score:.1f}/10.",
                signal=signal, evidenceRefs=event_refs, cautious=mastery.confidence == "low")]
            evidence.extend(ContextEvidence(ref=ref, kind="mastery_event", observedAt=event.created_at,
                summary=f"Topic mastery changed to {float(event.new_score):.1f}/10 from published assessed work.")
                for ref, event in zip(event_refs, events))
        attempts = []
        for result, question, assessment in db.execute(select(AssessmentResult, AssessmentQuestion, Assessment).join(
            AssessmentQuestion, AssessmentQuestion.id == AssessmentResult.question_id).join(
            Assessment, Assessment.id == AssessmentResult.assessment_id).where(
            Assessment.student_id == student_id, Assessment.subject_id == session.subject_id,
            AssessmentResult.status == "published").order_by(AssessmentResult.created_at.desc())).all():
            if str(topic.id) not in question.topic_ids:
                continue
            ref = _reference("assessment", result.id, result.version_number)
            missing = [str(item.get("rationale", ""))[:240] for item in result.marking_decisions
                       if not item.get("awarded")]
            attempts.append(ContextAttempt(evidenceRef=ref, observedAt=result.created_at, mode=assessment.mode,
                score=round(result.awarded_marks / result.max_marks * 10, 1),
                awardedMarks=result.awarded_marks, maxMarks=result.max_marks, markingSummary=missing[:8]))
            evidence.append(ContextEvidence(ref=ref, kind="assessment_result", observedAt=result.created_at,
                summary=f"Assessed {result.awarded_marks}/{result.max_marks} in {topic.title}."))
        mistakes = []
        for diagnosis in db.scalars(select(WeaknessDiagnosis).where(
            WeaknessDiagnosis.student_id == student_id, WeaknessDiagnosis.topic_id == topic.id
        ).order_by(WeaknessDiagnosis.created_at)).all():
            ref = _reference("mistake", diagnosis.id)
            statement = ContextStatement(text=f"AKURU found {diagnosis.category.replace('_', ' ')} in {topic.title}.",
                signal="recurring_mistake", evidenceRefs=[ref], cautious=diagnosis.confidence < .75)
            mistakes.append(ContextMistakePattern(topic=topic.title, category=diagnosis.category,
                last7Days=int(diagnosis.created_at >= generated_at - timedelta(days=7)),
                last30Days=int(diagnosis.created_at >= generated_at - timedelta(days=30)),
                lifetime=diagnosis.occurrence_number, evidenceRefs=[ref], statement=statement))
            evidence.append(ContextEvidence(ref=ref, kind="mistake", observedAt=diagnosis.created_at,
                summary=diagnosis.description))
        recommendations, recommendation_evidence = _reviewed_recommendations(
            db, student_id, session.subject_id, topic.id)
        plans, plan_evidence = _plan_items(db, student_id, session.subject_id, topic.id)
        evidence.extend(recommendation_evidence + plan_evidence)
        dimensions = ({row.dimension: float(row.score) for row in db.scalars(select(
            TopicMasteryDimension).where(TopicMasteryDimension.mastery_id == mastery.id)).all()}
            if mastery and events else {})
        topics.append(ContextTopic(topic=PlanTopicResponse(topicRef=topic.public_ref, code=topic.code,
            title=topic.title, groupRef=group.public_ref, groupCode=group.code, groupTitle=group.title),
            active=topic.id == session.active_topic_id,
            masteryScore=float(mastery.display_score) if mastery and events else None,
            confidence=mastery.confidence if mastery and events else None,
            trend=float(mastery.trend) if mastery and events else None, evidenceCount=len(events),
            varietyCount=mastery.variety_count if mastery and events else 0, dimensions=dimensions,
            signals=signals, statements=statements, attempts=attempts[:10], mistakes=mistakes,
            reviewedRecommendations=recommendations, studyPlan=plans))
    evidence = list({row.ref: row for row in evidence}.values())
    evidence.sort(key=lambda row: row.ref)
    digest = hashlib.sha256("|".join([CONTEXT_ALGORITHM, session.subject_id, active.public_ref]
        + [item.ref for item in evidence]).encode()).hexdigest()
    active_response = next(row.topic for row in topics if row.active)
    provider = ProviderLearnerContext(
        learnerRef="learner_" + hashlib.sha256(f"akuru:{student_id}".encode()).hexdigest()[:20],
        subjectId=session.subject_id, activeTopicCode=active.code, contextVersion=digest,
        learningSignals=[{"topicRef": item.topic.topicRef, "group": item.topic.groupTitle,
            "signals": item.signals, "statements": [value.model_dump(mode="json") for value in item.statements]}
            for item in topics],
        recurringMistakes=[{"topicRef": item.topic.topicRef, "topic": pattern.topic,
            "last7Days": pattern.last7Days, "evidenceRefs": pattern.evidenceRefs}
            for item in topics for pattern in item.mistakes],
        reviewedRecommendations=[{"topicRef": item.topic.topicRef, "title": recommendation.title,
            "activityType": recommendation.activityType, "evidenceRef": recommendation.evidenceRef}
            for item in topics for recommendation in item.reviewedRecommendations],
        plannedActivities=[{"topicRef": item.topic.topicRef, "title": plan.title,
            "activityType": plan.activityType, "evidenceRef": plan.evidenceRef}
            for item in topics for plan in item.studyPlan],
    )
    return LearnerContextResponse(operationRef=operation_ref, contextVersion=digest,
        generatedAt=generated_at, subjectId=session.subject_id, activeTopic=active_response,
        topics=topics, evidence=evidence, providerContext=provider)


def build_and_log(db: Session, settings: Settings, principal: Principal, session_ref: str, request_key: str):
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TEXT)
    session = tutor_sessions._owned_session(db, principal.user.id, session_ref, lock=True)
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS,
                         session.subject_id, "tutor_learner_context")
    if session.status != "active":
        raise DomainError("tutor_session_ended", "This tutor session has ended.", 409)
    existing = db.scalar(select(TutorLearnerContextLog).where(
        TutorLearnerContextLog.session_id == session.id,
        TutorLearnerContextLog.request_key == request_key))
    if existing:
        return LearnerContextResponse.model_validate(existing.context_snapshot)
    operation_ref = f"tutor_context_{uuid.uuid4().hex}"
    payload = _build(db, principal.user.id, session, operation_ref, _now())
    db.add(TutorLearnerContextLog(public_ref=operation_ref, session_id=session.id,
        student_id=principal.user.id, subject_id=session.subject_id,
        active_topic_id=session.active_topic_id, request_key=request_key,
        context_version=payload.contextVersion,
        evidence_references=[item.ref for item in payload.evidence],
        context_snapshot=payload.model_dump(mode="json")))
    db.commit()
    return payload
