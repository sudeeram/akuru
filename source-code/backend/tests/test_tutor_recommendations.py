from datetime import datetime, timezone

from app.schemas.curriculum_plans import PlanUnitResponse
from app.schemas.tutor_context import ContextPlanItem, ContextReviewedRecommendation, ContextUnit
from app.services.tutor_recommendations import _rank, _ranking_key


def _unit(code: str) -> ContextUnit:
    return ContextUnit(unit=PlanUnitResponse(id=f"00000000-0000-0000-0000-0000000000{code[-2:]}", code=code, title=code), active=False)


def test_reviewed_recommendations_plan_and_assessment_are_ranked_with_evidence():
    unit = _unit("U01")
    unit.reviewedRecommendations = [ContextReviewedRecommendation(evidenceRef="recommendation:1",
        title="Review equations", activityType="review", reason="Reviewed evidence", action="Read and retry",
        successCondition="Answer correctly")]
    unit.studyPlan = [ContextPlanItem(evidenceRef="plan:1", title="Equation practice",
        activityType="targeted_practice", status="planned", scheduledFor=datetime.now(timezone.utc))]
    ranked, _ = _rank(unit, ["assessment_blueprint:1"], 0)
    assert {item.factor for item in ranked.factors} == {
        "mastery_evidence_gap", "reviewed_recommendations", "current_study_plan", "current_term_assessment"
    }
    assert {"recommendation:1", "plan:1", "assessment_blueprint:1"}.issubset(ranked.evidenceRefs)


def test_ties_use_stable_curriculum_sequence_then_code():
    first = _rank(_unit("U01"), [], 0)
    second = _rank(_unit("U02"), [], 1)
    assert sorted([second, first], key=_ranking_key)[0][0].unit.code == "U01"
