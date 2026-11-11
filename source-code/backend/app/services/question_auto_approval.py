"""Server-only confidence approval; never changes human decisions or release switches."""
from copy import deepcopy
from sqlalchemy import select
from app.errors import DomainError
from app.models import AuditEvent, OfficialPaperReviewQuestion, OfficialQuestionAnalysis
from app.schemas.official_paper_reviews import ReviewQuestionData

THRESHOLD = 75
POLICY = "accuracy-auto-approval-v1"
APPROVED = {"approved", "ai_approved"}


def current_accuracy(db, workspace, question):
    from .official_question_analyses import content_hash, source_manifest
    row = db.scalar(select(OfficialQuestionAnalysis).where(
        OfficialQuestionAnalysis.question_id == question.id,
        OfficialQuestionAnalysis.stage == "accuracy").order_by(OfficialQuestionAnalysis.version_number.desc()).limit(1))
    if not row or row.content_hash != content_hash(db, question, source_manifest(db, workspace)):
        return None
    return row


def qualifies(analysis, labels):
    if not analysis or analysis.analysis_data["question"]["percent"] <= THRESHOLD:
        return False
    parts = analysis.analysis_data["parts"]
    return bool(labels) and {p["label"] for p in parts} == set(labels) and all(p["percent"] > THRESHOLD for p in parts)


def is_approved(db, workspace, question):
    if question.status == "approved":
        return True
    if question.status != "ai_approved":
        return False
    data = ReviewQuestionData.model_validate(question.review_data)
    if not qualifies(current_accuracy(db, workspace, question), [p.label for p in data.parts]):
        return False
    from .official_paper_reviews import _validate_question
    try:
        _validate_question(db, workspace, "ai_approved", data, question.review_data, question.number)
    except DomainError:
        return False
    return True


def apply(db, principal, workspace, question):
    """Apply the latest bound accuracy analysis. Missing review requirements fail closed."""
    from .official_paper_reviews import _validate_question
    if question.status in {"approved", "excluded", "needs_correction"}:
        return {"number": question.number, "status": question.status, "changed": False, "reason": "Human decision preserved."}
    before = (question.status, deepcopy(question.review_data))
    data = ReviewQuestionData.model_validate(question.review_data)
    if question.status == "ai_approved":
        question.status = "unreviewed"
    for part in data.parts:
        if part.status == "ai_approved":
            part.status = "unreviewed"
    analysis = current_accuracy(db, workspace, question)
    scores = {p["label"]: p["percent"] for p in analysis.analysis_data["parts"]} if analysis else {}
    blockers = []
    for part in data.parts:
        if part.status not in {"unreviewed", "ready_for_approval"} or scores.get(part.label, 0) <= THRESHOLD:
            continue
        previous = part.status
        part.status = "ai_approved"
        try:
            _validate_question(db, workspace, "unreviewed", data, question.review_data, question.number)
        except DomainError as exc:
            part.status = previous
            blockers.append(exc.message if exc.message.startswith('Part ') else f"Part {part.label or '(whole question)'}: {exc.message}")
    if qualifies(analysis, [p.label for p in data.parts]) and all(p.status in APPROVED for p in data.parts):
        try:
            _validate_question(db, workspace, "ai_approved", data, question.review_data, question.number)
            question.status = "ai_approved"
        except DomainError as exc:
            blockers.append(exc.message)
    question.review_data = data.model_dump(mode="json")
    changed = before != (question.status, question.review_data)
    if changed:
        question.revision += 1
        # reviewed_by/at remain the last human edit, never impersonate a human approver.
        db.add(AuditEvent(actor_id=principal.user.id, action="official_review.ai_approval_evaluated",
            target_type="official_paper_review_question", target_id=str(question.id), event_data={
                "policy": POLICY, "thresholdExclusive": THRESHOLD,
                "analysisId": str(analysis.id) if analysis else None,
                "contentHash": analysis.content_hash if analysis else None,
                "previousStatus": before[0], "status": question.status,
                "parts": [{"label": p.label, "status": p.status} for p in data.parts],
                "blockers": blockers}))
    return {"number": question.number, "status": question.status, "changed": changed,
        "reason": "; ".join(dict.fromkeys(blockers)) or (
            "No current accuracy assessment. Reassess the saved source evidence before AI approval." if not analysis else
            "Current confidence must exceed 75% for the question and every subpart."
            if not qualifies(analysis, [p.label for p in data.parts]) else "Confidence and review requirements passed.")}


def apply_paper(db, principal, paper_id):
    from .official_paper_reviews import _workspace, _validate_bound_versions
    workspace = _workspace(db, paper_id)
    _validate_bound_versions(db, workspace)
    questions = db.scalars(select(OfficialPaperReviewQuestion).where(
        OfficialPaperReviewQuestion.workspace_id == workspace.id).order_by(
        OfficialPaperReviewQuestion.number).with_for_update()).all()
    results = [apply(db, principal, workspace, question) for question in questions]
    db.commit()
    return {"policy": POLICY, "thresholdExclusive": THRESHOLD, "results": results}
