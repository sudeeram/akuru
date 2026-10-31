"""Validate private scheme crops and serve only frozen, released model answers."""
import uuid
from sqlalchemy import select
from app.errors import DomainError
from app.models import DocumentAsset, AssessmentQuestion


def validate_visuals(db, version_id, visuals, codes=None, part_label=None, question_number=None):
    seen = set()
    for visual in visuals:
        asset = db.get(DocumentAsset, visual.assetId)
        if (not asset or asset.document_version_id != version_id
                or not asset.asset_metadata.get("answerVisual")
                or not (asset.asset_metadata.get("reviewCrop") or asset.asset_metadata.get("generatedAnswer"))):
            raise DomainError("invalid_answer_visual", "Choose a dedicated crop from this paper's exact marking scheme.", 422)
        generated = asset.asset_metadata.get("generatedAnswer", False)
        if generated:
            import hashlib, json
            from app.models import GeneratedWorkedAnswer, OfficialPaperReviewQuestion, OfficialPaperReviewWorkspace
            from app.services.worked_answers.lifecycle import fingerprint
            row = db.get(GeneratedWorkedAnswer, visual.workedAnswerId) if visual.workedAnswerId else None
            q = db.get(OfficialPaperReviewQuestion, row.question_id) if row else None
            w = db.get(OfficialPaperReviewWorkspace, q.workspace_id) if q else None
            if (visual.origin != "ai_generated" or not row or not w or row.status != "approved"
                    or (question_number is not None and q.number != question_number)
                    or asset.asset_metadata.get("workedAnswerId") != str(row.id)
                    or asset.asset_metadata.get("partLabel") != visual.partLabel
                    or fingerprint(db, w, q)[0] != row.source_hash
                    or asset.asset_metadata.get("sourceHash") != row.source_hash
                    or asset.asset_metadata.get("solutionHash") != hashlib.sha256(json.dumps(row.solution,sort_keys=True).encode()).hexdigest()
                    or visual.explanation != asset.asset_metadata.get("explanation")
                    or visual.limitations != asset.asset_metadata.get("limitations")
                    or visual.dataText != asset.asset_metadata.get("dataText")):
                raise DomainError("generated_answer_stale", "Use a current, approved generated answer with its original label.", 409)
        elif visual.origin != "official_scheme" or visual.workedAnswerId:
            raise DomainError("invalid_answer_origin", "Official scheme crops cannot be labelled as generated answers.", 422)
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
    if not question or question.assessment_id != assessment.id:
        raise DomainError("answer_visual_not_found", "Model answer is not available.", 404)
    revealed = False
    from app.services.assessments import _now
    if getattr(assessment, "mode", None) == "practice" and assessment.status == "active" and assessment.ends_at > _now():
        from app.models import AssessmentInteraction
        revealed = bool(db.scalar(select(AssessmentInteraction.id).where(
            AssessmentInteraction.assessment_id == assessment.id,
            AssessmentInteraction.question_id == question.id,
            AssessmentInteraction.kind == "worked_answer")))
    if not revealed and (not assessment.submitted_at or assessment.status not in {"submitted", "expired"}):
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


def reveal_worked_answer(db, principal, assessment_id, question_id):
    from app.services.assessments import _owned, _now
    from app.services.assessment_access import require_practice_assistance
    from app.models import AssessmentInteraction
    assessment = _owned(db, principal, assessment_id, True)
    require_practice_assistance(assessment.mode, assistance="Worked answers")
    if assessment.status != "active" or assessment.ends_at <= _now():
        raise DomainError("assessment_deadline_passed", "Practice has ended. Use released feedback instead.", 409)
    question = db.get(AssessmentQuestion, question_id)
    if not question or question.assessment_id != assessment.id:
        raise DomainError("assessment_question_not_found", "Question not found.", 404)
    visuals = [v for v in question.rubric.get("answerVisuals", []) if v.get("status") == "approved" and v.get("origin") == "ai_generated"]
    if not visuals:
        raise DomainError("worked_answer_unavailable", "No approved generated worked answer is released for this question yet.", 409)
    existing = db.scalar(select(AssessmentInteraction.id).where(AssessmentInteraction.assessment_id == assessment.id,
        AssessmentInteraction.question_id == question.id, AssessmentInteraction.kind == "worked_answer"))
    if not existing:
        db.add(AssessmentInteraction(assessment_id=assessment.id, question_id=question.id,
            student_id=principal.user.id, kind="worked_answer", request_key="worked-answer-reveal"))
        db.commit()
    return {"visuals": visuals, "assisted": True, "message": "This question is now assisted practice and will not increase independent mastery."}
