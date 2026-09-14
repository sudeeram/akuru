"""Human review creates a new result and retains the original AI evidence."""
import copy
import uuid
from sqlalchemy import select
from app.errors import DomainError
from app.models import Assessment, AssessmentResult, AssessmentQuestion, AuditEvent, StudentProfile, ImprovementRecommendation, WeaknessDiagnosis
from app.services import assessment_marking, mastery, weaknesses


def review(db, principal, result_id, payload):
    original = db.get(AssessmentResult, result_id)
    if not original:
        raise DomainError("result_not_found", "Assessment result not found.", 404)
    assessment = db.scalar(select(Assessment).where(Assessment.id == original.assessment_id).with_for_update())
    profile = db.get(StudentProfile, assessment.student_id)
    if principal.user.role not in {"parent", "admin"} or (principal.user.role == "parent" and profile.parent_id != principal.user.id):
        raise DomainError("result_not_found", "Assessment result not found.", 404)
    key = "review:" + payload.idempotencyKey[:93]
    existing = db.scalar(select(AssessmentResult).where(AssessmentResult.question_id == original.question_id, AssessmentResult.request_key == key))
    if existing:
        db.commit()
        return assessment_marking.result_response(existing)
    latest = assessment_marking.latest_results(db, assessment.id)[original.question_id]
    if latest.id != original.id:
        raise DomainError("review_stale", "A newer result exists. Refresh and review the latest result.", 409)
    question = db.get(AssessmentQuestion, original.question_id)
    marks = assessment_marking._validate(payload.markingDecisions, assessment_marking._official_points(question), question.marks)
    values = {column.name: copy.deepcopy(getattr(original, column.name)) for column in AssessmentResult.__table__.columns if column.name not in {"id", "created_at"}}
    values.update(version_number=original.version_number + 1, request_key=key, status="published",
        awarded_marks=marks, marking_decisions=[point.model_dump() for point in payload.markingDecisions],
        teaching_explanation=payload.feedback, improved_answer=payload.improvedAnswer,
        strengths=payload.strengths, small_mistakes=payload.smallMistakes, conceptual_mistakes=payload.conceptualMistakes,
        review_reasons=[], recommendations=[], unit_evidence=[])
    # Confidence remains the original model confidence; a human decision is not a new probability estimate.
    values["source_manifest"].append({"type": "human_review", "originalResultId": str(original.id),
        "reviewerId": str(principal.user.id), "reviewerRole": principal.user.role, "reason": payload.reason})
    result = AssessmentResult(**values)
    db.add(result); db.flush()
    db.add(AuditEvent(actor_id=principal.user.id, action="assessment.review", target_type="assessment_result",
        target_id=str(result.id), event_data={"originalResultId": str(original.id), "reason": payload.reason}))
    old_recommendations = db.scalars(select(ImprovementRecommendation).join(WeaknessDiagnosis,
        WeaknessDiagnosis.id == ImprovementRecommendation.diagnosis_id).where(
        WeaknessDiagnosis.question_id == original.question_id)).all()
    for recommendation in old_recommendations:
        recommendation.review_status = "rejected"
        recommendation.review_reason = "Superseded by a human-reviewed assessment result."
    mastery.record_result(db, result, commit=False)
    weaknesses.record_result(db, result, commit=False)
    db.commit(); db.refresh(result)
    return assessment_marking.result_response(result)
