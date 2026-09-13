import hashlib
import json
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.base import AIProviderError, AIRequest, AIResult
from app.ai.prompts import get_prompt
from app.ai.router import AIAccountRouter
from app.config import Settings
from app.errors import DomainError
from app.models import Assessment, AssessmentAnswer, AssessmentQuestion, AssessmentResult, Document, RetrievalChunk, TextbookUnit
from app.schemas.assessments import AssessmentPassOne, AssessmentPassTwo


SCHEMA_VERSION = "assessment-result-v1"


def _official_points(question: AssessmentQuestion) -> list[dict]:
    points = []
    for index, raw in enumerate(question.rubric.get("markingPoints", []), 1):
        value = raw if isinstance(raw, dict) else {"text": str(raw)}
        criterion = str(value.get("text") or value.get("criterion") or "").strip()
        if not criterion:
            continue
        marks = int(value.get("marks") or value.get("maxMarks") or 1)
        points.append({"pointId": str(value.get("code") or value.get("markCode") or f"P{index}"),
                       "criterion": criterion, "maxMarks": marks})
    if not points:
        raise DomainError("assessment_rubric_required", "This question has no approved marking points and cannot be assessed automatically.", 409)
    if sum(point["maxMarks"] for point in points) > question.marks:
        raise DomainError("assessment_rubric_invalid", "The approved marking points exceed the question maximum.", 409)
    return points


def _sources(db: Session, question: AssessmentQuestion, limit: int) -> list[dict]:
    manifest = [{"type": "frozen_question", "questionVersionId": str(question.source_question_version_id),
                 "documentVersionId": str(question.source_document_version_id), "locations": question.source_locations},
                {"type": "frozen_rubric", "rubric": question.rubric}]
    unit_ids = [uuid.UUID(value) for value in question.unit_ids]
    rows = db.execute(select(RetrievalChunk, Document, TextbookUnit).join(
        Document, Document.id == RetrievalChunk.document_id).join(
        TextbookUnit, TextbookUnit.id == RetrievalChunk.unit_id).where(
        RetrievalChunk.status == "active", RetrievalChunk.subject_id == db.get(Assessment, question.assessment_id).subject_id,
        RetrievalChunk.unit_id.in_(unit_ids), RetrievalChunk.source_type == "textbook_section",
        Document.review_state == "published", Document.removed_at.is_(None),
    ).order_by(RetrievalChunk.unit_id, RetrievalChunk.page_number, RetrievalChunk.source_ordinal).limit(limit)).all()
    for chunk, document, unit in rows:
        manifest.append({"type": "textbook_context", "chunkId": str(chunk.id), "documentId": str(document.id),
                         "documentVersionId": str(chunk.document_version_id), "documentTitle": document.title,
                         "unitId": str(unit.id), "unitCode": unit.unit_code, "unitTitle": unit.title,
                         "page": chunk.page_number, "boundingBox": chunk.bounding_box,
                         "contentHash": chunk.content_hash, "content": chunk.content})
    return manifest


def _task(question: AssessmentQuestion, answer: AssessmentAnswer | None, points: list[dict], sources: list[dict], pass_one: dict | None = None) -> str:
    command_word = question.prompt.strip().split(" ", 1)[0] if question.prompt.strip() else "Answer"
    payload = {"question": {"number": question.question_number, "sharedStem": question.shared_stem,
        "prompt": question.prompt, "maximumMarks": question.marks, "commandWord": command_word,
        "equations": question.equations}, "studentAnswer": answer.answer_text if answer else "",
        "studentFileId": answer.file_id if answer else None, "officialMarkingPoints": points,
        "acceptedAlternatives": question.rubric.get("alternatives", []),
        "examinerAdvice": question.rubric.get("examinerAdvice", []),
        "commonMistakes": question.rubric.get("commonMistakes", []), "sourceEvidence": sources}
    if pass_one is not None:
        payload["firstPassDecisions"] = pass_one
        payload["instruction"] = "Reconcile the first-pass decisions, then produce concise exam-ready and teaching feedback. Keep official point IDs and criteria unchanged."
    else:
        payload["instruction"] = "Decide every official marking point independently from meaning and method. Quote or precisely identify student evidence even when the point is missed."
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def _generate(db: Session, settings: Settings, request: AIRequest) -> AIResult:
    return AIAccountRouter(db, settings).generate(request)


def _validate(decisions, points: list[dict], question_marks: int) -> int:
    expected = {point["pointId"]: point for point in points}
    if len(decisions) != len(expected) or set(row.pointId for row in decisions) != set(expected):
        raise DomainError("assessment_output_invalid", "AKURU did not assess every approved marking point exactly once.", 422)
    total = 0
    for row in decisions:
        point = expected[row.pointId]
        if row.criterion != point["criterion"] or row.maxMarks != point["maxMarks"]:
            raise DomainError("assessment_output_invalid", "AKURU changed an approved marking point.", 422)
        total += row.marksAwarded
    if total > question_marks:
        raise DomainError("assessment_output_invalid", "AKURU attempted to award more than the question maximum.", 422)
    return total


def result_response(row: AssessmentResult) -> dict:
    return {"id": row.id, "version": row.version_number, "status": row.status,
            "awardedMarks": row.awarded_marks, "maxMarks": row.max_marks, "confidence": row.confidence,
            "markingDecisions": row.marking_decisions, "strengths": row.strengths,
            "smallMistakes": row.small_mistakes, "conceptualMistakes": row.conceptual_mistakes,
            "improvedAnswer": row.improved_answer, "teachingExplanation": row.teaching_explanation,
            "unitEvidence": row.unit_evidence, "recommendations": row.recommendations,
            "reviewReasons": row.review_reasons, "createdAt": row.created_at}


def latest_results(db: Session, assessment_id: uuid.UUID) -> dict[uuid.UUID, AssessmentResult]:
    rows = db.scalars(select(AssessmentResult).where(AssessmentResult.assessment_id == assessment_id).order_by(
        AssessmentResult.question_id, AssessmentResult.version_number.desc())).all()
    result = {}
    for row in rows:
        result.setdefault(row.question_id, row)
    return result


def evaluate(db: Session, settings: Settings, assessment: Assessment, request_key: str) -> None:
    if assessment.status not in {"submitted", "expired"}:
        raise DomainError("assessment_submission_required", "Submit the assessment before AKURU marks it.", 409)
    questions = db.scalars(select(AssessmentQuestion).where(AssessmentQuestion.assessment_id == assessment.id).order_by(AssessmentQuestion.sequence)).all()
    answers = {row.question_id: row for row in db.scalars(select(AssessmentAnswer).where(AssessmentAnswer.assessment_id == assessment.id)).all()}
    prompt = get_prompt("assessment")
    for question in questions:
        existing = db.scalar(select(AssessmentResult).where(AssessmentResult.assessment_id == assessment.id,
            AssessmentResult.question_id == question.id, AssessmentResult.request_key == request_key))
        if existing:
            continue
        answer = answers.get(question.id); points = _official_points(question)
        sources = _sources(db, question, settings.assessment_context_chunks)
        sources.append({"type": "assessment_prompt", "name": prompt.name, "version": prompt.version,
                        "instructions": prompt.instructions})
        material = json.dumps({"answer": answer.answer_text if answer else "", "file": answer.file_id if answer else None,
            "question": question.prompt, "rubric": question.rubric, "sources": sources}, sort_keys=True)
        input_hash = hashlib.sha256(material.encode()).hexdigest()
        metadata = {"assessment_id": str(assessment.id), "question_id": str(question.id), "subject_id": assessment.subject_id}
        try:
            first = _generate(db, settings, AIRequest(purpose=prompt.purpose, prompt_name=f"{prompt.name}-decisions",
                prompt_version=prompt.version, instructions=prompt.instructions, task=_task(question, answer, points, sources),
                output_type=AssessmentPassOne, metadata=metadata))
            _validate(first.output.decisions, points, question.marks)
            second = _generate(db, settings, AIRequest(purpose=prompt.purpose, prompt_name=f"{prompt.name}-feedback",
                prompt_version=prompt.version, instructions=prompt.instructions, task=_task(question, answer, points, sources, first.output.model_dump()),
                output_type=AssessmentPassTwo, metadata=metadata))
        except AIProviderError as exc:
            raise DomainError(exc.code, str(exc), 503) from exc
        awarded = _validate(second.output.decisions, points, question.marks)
        if [(d.pointId, d.awarded, d.marksAwarded) for d in first.output.decisions] != [(d.pointId, d.awarded, d.marksAwarded) for d in second.output.decisions]:
            raise DomainError("assessment_reconciliation_failed", "The two marking passes disagreed; this answer requires a new assessment.", 422)
        confidence = min(first.output.overallConfidence, second.output.confidence, *(d.confidence for d in second.output.decisions))
        review = list(dict.fromkeys(first.output.reviewReasons + second.output.reviewReasons))
        if answer and answer.file_id:
            review.append("Attached working requires human review until handwriting extraction is available.")
        if confidence < settings.assessment_confidence_threshold:
            review.append(f"Confidence {confidence:.2f} is below the {settings.assessment_confidence_threshold:.2f} publication threshold.")
        if assessment.subject_id == "english" and confidence < 0.9:
            review.append("Subjective English response requires review below 0.90 confidence.")
        version = (db.scalar(select(func.max(AssessmentResult.version_number)).where(AssessmentResult.question_id == question.id)) or 0) + 1
        row = AssessmentResult(assessment_id=assessment.id, question_id=question.id, version_number=version,
            schema_version=SCHEMA_VERSION, status="needs_review" if review else "published",
            answer_revision=answer.save_revision if answer else 0, input_hash=input_hash, request_key=request_key,
            awarded_marks=awarded, max_marks=question.marks, confidence=confidence,
            marking_decisions=[d.model_dump() for d in second.output.decisions], strengths=second.output.strengths,
            small_mistakes=second.output.smallMistakes, conceptual_mistakes=second.output.conceptualMistakes,
            improved_answer=second.output.improvedAnswer, teaching_explanation=second.output.teachingExplanation,
            unit_evidence=second.output.unitEvidence, recommendations=second.output.recommendations,
            review_reasons=review, provider=second.provider, model=second.model, prompt_name=prompt.name,
            prompt_version=prompt.version, rubric_snapshot=question.rubric, source_manifest=sources,
            pass_one_output=first.output.model_dump(), pass_two_output=second.output.model_dump())
        db.add(row); db.commit()
