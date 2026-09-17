import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import DomainError
from app.models import AssessmentBlueprint, StudentProgression
from app.schemas.tutor_recommendations import (
    NextTopicRecommendation, NextTopicResponse, RankedTopic, RankingFactor,
    RecommendationActivity, TutorRecommendationBrief,
)
from app.security import Principal
from app.services import curriculum_plans, tutor_context, tutor_sessions
from app.services.assessment_access import TutorCapability, require_tutor_access


ALGORITHM_VERSION = "next-topic-v2"


def _factor(name: str, points: float, explanation: str, refs=()) -> RankingFactor:
    return RankingFactor(factor=name, points=round(points, 2), explanation=explanation,
                         evidenceRefs=list(refs))


def _activity(unit) -> RecommendationActivity:
    target = unit.topic
    planned = next((item for item in unit.studyPlan if item.status == "planned"), None)
    if planned:
        return RecommendationActivity(type=planned.activityType, title=planned.title,
            instruction=f"Complete the planned {planned.activityType.replace('_', ' ')} activity.",
            successCondition="Complete the activity and check the next assessed result.")
    if unit.reviewedRecommendations:
        item = unit.reviewedRecommendations[0]
        return RecommendationActivity(type=item.activityType, title=item.title,
            instruction=item.action, successCondition=item.successCondition)
    if unit.mistakes:
        return RecommendationActivity(type="targeted_practice", title=f"Practise {unit.mistakes[0].topic}",
            instruction="Answer a short set of eligible questions about this recurring mistake.",
            successCondition="Answer the targeted questions correctly without hints.")
    if "low_confidence" in unit.signals or "insufficient_evidence" in unit.signals:
        return RecommendationActivity(type="unit_check", title=f"Check {target.code}",
            instruction="Complete a short eligible topic check to gather reliable evidence.",
            successCondition="Complete the check without tutor hints.")
    return RecommendationActivity(type="review", title=f"Review {target.title}",
        instruction="Review the assessed mistakes, then explain the key idea in your own words.",
        successCondition="Explain the idea and complete one eligible practice question.")


def _rank(unit, blueprint_refs: list[str], sequence: int) -> tuple[RankedTopic, int]:
    factors = []
    evidence_refs = {ref for statement in unit.statements for ref in statement.evidenceRefs}
    has_learner_evidence = bool(unit.attempts or unit.mistakes or unit.reviewedRecommendations or unit.studyPlan or unit.masteryScore is not None)
    if unit.masteryScore is not None:
        refs = [ref for statement in unit.statements if statement.signal in {"strong", "weak", "improving", "declining", "low_confidence"} for ref in statement.evidenceRefs]
        points = (10 - unit.masteryScore) * 8
        factors.append(_factor("mastery_gap", points, f"Mastery is {unit.masteryScore:.1f}/10.", refs))
    elif has_learner_evidence:
        factors.append(_factor("mastery_evidence_gap", 12, "More assessed mastery evidence is needed.", evidence_refs))
    if "low_confidence" in unit.signals:
        factors.append(_factor("low_confidence", 12, "Current mastery confidence is low or evidence is limited.", evidence_refs))
    if "declining" in unit.signals:
        factors.append(_factor("declining_trend", 14, "Recent mastery is declining.", evidence_refs))
    elif "improving" in unit.signals:
        factors.append(_factor("improving_trend", -4, "Recent improvement reduces immediate priority.", evidence_refs))
    recent_mistake_refs = [ref for item in unit.mistakes for ref in item.evidenceRefs]
    recent_mistakes = sum(item.last7Days for item in unit.mistakes)
    older_mistakes = max(0, sum(item.last30Days for item in unit.mistakes) - recent_mistakes)
    if recent_mistakes or older_mistakes:
        points = min(24, recent_mistakes * 4) + min(8, older_mistakes * 2)
        factors.append(_factor("recurring_assessed_mistakes", points,
            f"{recent_mistakes} assessed mistakes in 7 days and {older_mistakes} additional mistakes in 30 days.", recent_mistake_refs))
    recommendation_refs = [item.evidenceRef for item in unit.reviewedRecommendations]
    if recommendation_refs:
        factors.append(_factor("reviewed_recommendations", min(16, len(recommendation_refs) * 8),
            f"{len(recommendation_refs)} reviewed improvement recommendation(s) apply.", recommendation_refs))
    plan_refs = [item.evidenceRef for item in unit.studyPlan if item.status == "planned"]
    if plan_refs:
        factors.append(_factor("current_study_plan", min(20, len(plan_refs) * 10),
            f"{len(plan_refs)} current planned activity item(s) apply.", plan_refs))
    if blueprint_refs:
        factors.append(_factor("current_term_assessment", 5,
            "A published assessment blueprint exists for this subject and current term.", blueprint_refs))
    score = round(sum(item.points for item in factors), 2)
    evidence_refs.update(ref for factor in factors for ref in factor.evidenceRefs)
    return RankedTopic(topic=unit.topic, score=score, factors=factors,
                      evidenceRefs=sorted(evidence_refs)), sequence


def _ranking_key(item: tuple[RankedTopic, int]):
    return (-item[0].score, item[1], item[0].topic.code, item[0].topic.topicRef)


def recommend(db: Session, settings: Settings, principal: Principal, session_ref: str, subject_id: str, request_key: str):
    session = tutor_sessions._owned_session(db, principal.user.id, session_ref)
    if session.status != "active":
        raise DomainError("tutor_session_ended", "This tutor session has ended.", 409)
    if subject_id != session.subject_id:
        raise DomainError("tutor_recommendation_subject_mismatch",
                          "Recommendations must stay inside the active tutor subject.", 422)
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS,
                         session.subject_id, "tutor_next_topic")
    coverage = curriculum_plans.student_coverage(db, principal.user.id, subject_id)
    if coverage.status != "ready" or not coverage.coveredTopics:
        return NextTopicResponse(status="no_eligible_topics",
            message="No eligible covered topics are available for this subject.", algorithmVersion=ALGORITHM_VERSION)
    context = tutor_context.build_and_log(db, settings, principal, session_ref, request_key)
    progression = db.scalar(select(StudentProgression).where(
        StudentProgression.student_id == principal.user.id,
        StudentProgression.course_id == "igcse", StudentProgression.is_current.is_(True)))
    blueprints = db.scalars(select(AssessmentBlueprint).where(
        AssessmentBlueprint.course_id == "igcse", AssessmentBlueprint.subject_id == subject_id,
        AssessmentBlueprint.grade == (progression.grade if progression else -1),
        AssessmentBlueprint.term == (progression.term if progression else -1),
        AssessmentBlueprint.status == "published").order_by(AssessmentBlueprint.id)).all()
    blueprint_refs = [f"assessment_blueprint:{item.id}" for item in blueprints]
    scopes=context.topics
    ranked_pairs = [_rank(unit, blueprint_refs, index) for index, unit in enumerate(scopes)]
    ranked_pairs.sort(key=_ranking_key)
    ranking = [item[0] for item in ranked_pairs]
    if not any(unit.attempts or unit.mistakes or unit.reviewedRecommendations or unit.studyPlan or unit.masteryScore is not None for unit in scopes):
        return NextTopicResponse(status="no_evidence",
            message="AKURU needs assessed work or a reviewed learning recommendation before choosing a next topic.",
            algorithmVersion=ALGORITHM_VERSION, contextOperationRef=context.operationRef,
            contextVersion=context.contextVersion, ranking=ranking)
    chosen = ranking[0]
    source_unit=next(item for item in scopes if item.topic.topicRef==chosen.topic.topicRef)
    activity = _activity(source_unit)
    positive = [factor.explanation for factor in chosen.factors if factor.points > 0]
    reason = " ".join(positive) or "This topic has the highest deterministic priority from current evidence."
    recommendation = NextTopicRecommendation(topic=chosen.topic, reason=reason,
        evidenceRefs=chosen.evidenceRefs, activity=activity, requiresStudentAction=True,
        moveAction={"endpoint": f"/api/v1/tutoring/sessions/{session_ref}/switch-topic",
                    "topicRef": chosen.topic.topicRef,
                    "requiresNewRequestKey": True})
    brief = TutorRecommendationBrief(
        instruction="Explain the fixed AKURU ranking conversationally. Do not change the topic, reason, counts or evidence.",
        fixedTopicRef=chosen.topic.topicRef,
        fixedReason=reason, evidenceRefs=chosen.evidenceRefs)
    return NextTopicResponse(status="ready", message="AKURU found the highest-priority eligible topic.",
        algorithmVersion=ALGORITHM_VERSION, contextOperationRef=context.operationRef,
        contextVersion=context.contextVersion, recommendation=recommendation, ranking=ranking,
        tutorBrief=brief)
