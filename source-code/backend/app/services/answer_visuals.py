"""Validate private scheme crops and serve only frozen, released model answers."""
import uuid
from sqlalchemy import select
from app.errors import DomainError
from app.models import DocumentAsset, AssessmentQuestion


def validate_visuals(db, version_id, visuals, codes=None, part_label=None):
    seen = set()
    for visual in visuals:
        asset = db.get(DocumentAsset, visual.assetId)
        if (not asset or asset.document_version_id != version_id
                or not asset.asset_metadata.get("answerVisual")
                or not asset.asset_metadata.get("reviewCrop")):
            raise DomainError("invalid_answer_visual", "Choose a dedicated crop from this paper's exact marking scheme.", 422)
        if visual.assetId in seen:
            raise DomainError("duplicate_answer_visual", "Attach each answer visual once per subpart.", 422)
        seen.add(visual.assetId)
        if codes is not None and not set(visual.pointCodes).issubset(codes):
            raise DomainError("invalid_answer_point", "Link the answer visual to marking points in this subpart.", 422)
        if part_label is not None and visual.partLabel != part_label:
            raise DomainError("invalid_answer_part", "The answer visual must belong to this subpart.", 422)


def download(db, storage, principal, assessment_id, question_id, asset_id):
    from app.services.assessments import _owned
    assessment = _owned(db, principal, assessment_id)
    question = db.get(AssessmentQuestion, question_id)
    if (not assessment.submitted_at or assessment.status not in {"submitted", "expired"}
            or not question or question.assessment_id != assessment.id):
        raise DomainError("answer_visual_not_found", "Model answer is not available.", 404)
    visual = next((v for v in question.rubric.get("answerVisuals", [])
                   if v.get("assetId") == str(asset_id) and v.get("status") == "approved"), None)
    if not visual:
        raise DomainError("answer_visual_not_found", "Model answer is not available.", 404)
    asset = db.get(DocumentAsset, uuid.UUID(visual["assetId"]))
    if not asset or not asset.asset_metadata.get("answerVisual"):
        raise DomainError("answer_visual_not_found", "Model answer is not available.", 404)
    return storage.get(asset.object_key, asset.mime_type)


def queue_manual_result(db, assessment, question, answer, points, request_key):
    """No fabricated OCR score or mastery event for an unsupported drawing."""
    import hashlib
    import json
    from sqlalchemy import func
    from app.models import AssessmentResult
    version = (db.scalar(select(func.max(AssessmentResult.version_number)).where(AssessmentResult.question_id == question.id)) or 0) + 1
    reason = "Inspect the original drawing and approved model-answer diagrams. Automatic diagram marking is not enabled."
    row = AssessmentResult(assessment_id=assessment.id, question_id=question.id, version_number=version,
        schema_version="assessment-result-v1", status="needs_review", answer_revision=answer.save_revision if answer else 0,
        input_hash=hashlib.sha256(json.dumps({"question":str(question.id),"revision":answer.save_revision if answer else 0,"drawings":answer.drawing_files if answer else {},"rubric":question.rubric},sort_keys=True).encode()).hexdigest(),
        request_key=request_key, awarded_marks=0, max_marks=question.marks, confidence=0,
        marking_decisions=[dict(pointId=p["pointId"], criterion=p["criterion"], maxMarks=p["maxMarks"],
            awarded=False, marksAwarded=0, studentEvidence="Original drawing awaiting human inspection.", rationale="Pending visual review; no mark has been decided.", confidence=0) for p in points],
        improved_answer="See the approved model-answer diagrams and marking requirements.",
        teaching_explanation="Your drawing is saved and awaiting review. No score has been released.",
        review_reasons=[reason], provider="manual", model="none", prompt_name="drawing-review", prompt_version="v1",
        rubric_snapshot=question.rubric, source_manifest=[{"type":"frozen_rubric", "rubric":question.rubric}, {"type":"submitted_drawings", "files":answer.drawing_files if answer else {}}],
        pass_one_output={}, pass_two_output={}, subject_engine="drawing", subject_engine_version="v1",
        deterministic_checks={"manualOnly":True, "scorePending":True})
    db.add(row)
    return row
