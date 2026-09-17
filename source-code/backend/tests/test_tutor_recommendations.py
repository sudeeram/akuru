from datetime import datetime, timezone

from app.schemas.curriculum_plans import PlanTopicResponse
from app.schemas.tutor_context import ContextPlanItem, ContextReviewedRecommendation, ContextTopic
from app.services.tutor_recommendations import _rank, _ranking_key


def _topic(code: str) -> ContextTopic:
    suffix = int(code[-2:])
    return ContextTopic(
        topic=PlanTopicResponse(
            topicRef=f"topic_{suffix}",
            code=code,
            title=code,
            groupRef="group_1",
            groupCode="U1",
            groupTitle="Unit 1",
        ),
        active=False,
    )


def test_reviewed_recommendations_plan_and_assessment_are_ranked_with_evidence():
    topic = _topic("T01")
    topic.reviewedRecommendations = [ContextReviewedRecommendation(
        evidenceRef="recommendation:1",
        title="Review equations",
        activityType="review",
        reason="Reviewed evidence",
        action="Read and retry",
        successCondition="Answer correctly",
    )]
    topic.studyPlan = [ContextPlanItem(
        evidenceRef="plan:1",
        title="Equation practice",
        activityType="targeted_practice",
        status="planned",
        scheduledFor=datetime.now(timezone.utc),
    )]
    ranked, _ = _rank(topic, ["assessment_blueprint:1"], 0)
    assert {item.factor for item in ranked.factors} == {
        "mastery_evidence_gap",
        "reviewed_recommendations",
        "current_study_plan",
        "current_term_assessment",
    }
    assert {"recommendation:1", "plan:1", "assessment_blueprint:1"}.issubset(ranked.evidenceRefs)


def test_ties_use_stable_curriculum_sequence_then_topic_code():
    first = _rank(_topic("T01"), [], 0)
    second = _rank(_topic("T02"), [], 1)
    assert sorted([second, first], key=_ranking_key)[0][0].topic.code == "T01"
