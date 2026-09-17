import uuid
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.errors import DomainError
from app.models import (Assessment, AssessmentQuestion, AssessmentResult, Document, ImprovementRecommendation,
    OfficialMaterialVersion, OfficialQuestionTopicMapping, OfficialQuestionVersion, RetrievalChunk,
    StudentProfile, Textbook, TextbookGroup, TextbookTopic, TopicMastery, WeaknessDiagnosis)
from app.schemas.weaknesses import RecommendationListResponse, RecommendationResponse
from app.services.curriculum_plans import student_coverage

TAXONOMY = {
    "maths": (("formula", "formula_selection", "method"), ("unit", "units", "accuracy"), ("graph", "graph_interpretation", "application"), ("calcul", "calculation_accuracy", "accuracy"), ("method", "method", "method")),
    "science": (("unit", "units", "accuracy"), ("graph", "graph_interpretation", "application"), ("variable", "experimental_variables", "application"), ("termin", "terminology", "knowledge"), ("explain", "causal_reasoning", "reasoning")),
    "biology": (("termin", "terminology", "knowledge"), ("explain", "causal_reasoning", "reasoning"), ("graph", "graph_interpretation", "application")),
    "chemistry": (("formula", "formula_selection", "method"), ("unit", "units", "accuracy"), ("termin", "terminology", "knowledge"), ("explain", "causal_reasoning", "reasoning")),
    "physics": (("formula", "formula_selection", "method"), ("unit", "units", "accuracy"), ("graph", "graph_interpretation", "application"), ("calcul", "calculation_accuracy", "accuracy")),
    "ict": (("termin", "terminology", "knowledge"), ("scenario", "scenario_application", "application"), ("advantage", "trade_off", "reasoning"), ("disadvantage", "trade_off", "reasoning")),
    "english": (("evidence", "evidence_selection", "application"), ("organis", "organisation", "communication"), ("language", "language_accuracy", "communication"), ("explain", "command_word_response", "reasoning")),
    "french": (("vocab", "vocabulary", "knowledge"), ("grammar", "language_accuracy", "accuracy"), ("communicat", "communication", "communication")),
    "human-biology": (("termin", "terminology", "knowledge"), ("explain", "causal_reasoning", "reasoning")),
}

def classify(subject_id, text, kind=None):
    value = text.lower()
    for token, category, dimension in TAXONOMY.get(subject_id, ()):
        if token in value: return category, dimension
    if kind in {"method", "accuracy", "communication"}: return kind, kind
    if any(word in value for word in ("describe", "state", "name", "define")): return "command_word_response", "knowledge"
    return "factual_knowledge", "knowledge"

def _eligible_topic_question(db, student_id, subject_id, topic_id):
    coverage = student_coverage(db, student_id, subject_id)
    refs = {row.topicRef for row in coverage.coveredTopics} if coverage.status == "ready" else set()
    allowed = set(db.scalars(select(TextbookTopic.id).where(TextbookTopic.public_ref.in_(refs))).all())
    if topic_id not in allowed: return None
    candidates = db.scalars(select(OfficialQuestionVersion).join(OfficialMaterialVersion,
        OfficialMaterialVersion.id == OfficialQuestionVersion.material_version_id).join(
        OfficialQuestionTopicMapping, OfficialQuestionTopicMapping.question_version_id == OfficialQuestionVersion.id).where(
        OfficialMaterialVersion.course_id == "igcse", OfficialMaterialVersion.subject_id == subject_id,
        OfficialMaterialVersion.kind == "past_paper", OfficialMaterialVersion.status == "published",
        OfficialQuestionVersion.mapping_status == "confirmed", OfficialQuestionTopicMapping.status == "confirmed",
        OfficialQuestionTopicMapping.topic_id == topic_id).order_by(OfficialQuestionVersion.id)).all()
    for candidate in candidates:
        mapped = set(db.scalars(select(OfficialQuestionTopicMapping.topic_id).where(
            OfficialQuestionTopicMapping.question_version_id == candidate.id,
            OfficialQuestionTopicMapping.status == "confirmed", OfficialQuestionTopicMapping.required.is_(True))).all())
        if mapped and mapped.issubset(allowed): return candidate
    return None

def record_result(db: Session, result: AssessmentResult, *, commit=True):
    if result.status != "published": return
    question = db.get(AssessmentQuestion, result.question_id); assessment = db.get(Assessment, result.assessment_id)
    raw = [(str(item), None, "minor") for item in result.small_mistakes] + [(str(item), None, "major") for item in result.conceptual_mistakes]
    points = {str(p.get("code")): p for p in question.rubric.get("markingPoints", []) if isinstance(p, dict)}
    for decision in result.marking_decisions:
        if not decision.get("awarded"):
            raw.append((f"{decision.get('criterion', '')}: {decision.get('rationale', '')}".strip(), points.get(str(decision.get("pointId")), {}).get("kind"), "moderate"))
    grouped = {}
    for text, kind, severity in raw:
        if not text: continue
        category, dimension = classify(assessment.subject_id, text, kind)
        grouped.setdefault(category, {"dimension": dimension, "severity": severity, "evidence": []})["evidence"].append(text)
    mapped_ids = [uuid.UUID(value) for value in question.topic_ids]
    for topic_id in mapped_ids:
        source = db.scalar(select(RetrievalChunk).join(Document, Document.id == RetrievalChunk.document_id).where(
            RetrievalChunk.topic_id == topic_id,
            RetrievalChunk.subject_id == assessment.subject_id,
            RetrievalChunk.source_type == "textbook_section", RetrievalChunk.status == "active",
            Document.review_state == "published", Document.removed_at.is_(None)).order_by(RetrievalChunk.page_number))
        candidate = _eligible_topic_question(db, assessment.student_id, assessment.subject_id, topic_id)
        for category, detail in grouped.items():
            if db.scalar(select(WeaknessDiagnosis.id).where(WeaknessDiagnosis.result_id == result.id,
                WeaknessDiagnosis.topic_id == topic_id,
                WeaknessDiagnosis.category == category)): continue
            count = (db.scalar(select(func.count()).select_from(WeaknessDiagnosis).where(
                WeaknessDiagnosis.student_id == assessment.student_id,
                WeaknessDiagnosis.topic_id == topic_id,
                WeaknessDiagnosis.category == category)) or 0) + 1
            diagnosis = WeaknessDiagnosis(student_id=assessment.student_id, subject_id=assessment.subject_id,
                topic_id=topic_id,
                result_id=result.id, question_id=question.id, category=category, dimension=detail["dimension"],
                severity=detail["severity"], description=f"AKURU observed {category.replace('_', ' ')} in this topic.",
                evidence={"items": detail["evidence"], "resultId": str(result.id)}, occurrence_number=count, confidence=result.confidence)
            db.add(diagnosis); db.flush()
            if not source:
                continue
            mastery = db.scalar(select(TopicMastery).where(TopicMastery.student_id == assessment.student_id,
                TopicMastery.topic_id == topic_id))
            needs_review = result.confidence < 0.85 or (assessment.subject_id in {"english", "french"} and detail["dimension"] == "communication") or bool(mastery and mastery.provisional)
            status = "pending_review" if needs_review else "approved"
            reason = "Low-confidence, provisional or subjective recommendation requires Parent/Admin review." if needs_review else ""
            repeated = " This has appeared more than once." if count > 1 else ""
            activities = [("review", "Review the approved explanation", "Read the linked textbook section and write three key points.", "Explain the idea correctly without looking."),
                ("targeted_practice", "Practise the missed skill", "Answer the linked eligible question using the feedback.", "Meet every relevant marking point."),
                ("spaced_retry", "Retry after a short gap", "Return to this skill after at least three days.", "Improve the previous mark without hints."),
                ("unit_check", "Complete a short unit check", "Use the linked eligible question as a short check.", "Score at least 70% without hints.")]
            for activity, title, action, success in activities:
                db.add(ImprovementRecommendation(diagnosis_id=diagnosis.id, student_id=assessment.student_id,
                    subject_id=assessment.subject_id, topic_id=topic_id, source_chunk_id=source.id,
                    activity_question_version_id=candidate.id if candidate and activity != "review" else None,
                    activity_type=activity, title=title, reason=diagnosis.description + repeated,
                    action=action, success_condition=success, review_status=status, review_reason=reason))
    if commit: db.commit()
    else: db.flush()

def _authorize(db, principal, student_id):
    if principal.user.role == "student" and principal.user.id != student_id: raise DomainError("student_access_denied", "Students may only view their own recommendations.", 403)
    if principal.user.role == "parent":
        profile = db.get(StudentProfile, student_id)
        if not profile or profile.parent_id != principal.user.id: raise DomainError("student_access_denied", "This student is not linked to your parent account.", 403)

def list_recommendations(db, principal, student_id=None):
    if principal.user.role != "admin":
        if not student_id: student_id = principal.user.id
        _authorize(db, principal, student_id)
    recommendations=[]
    topic_query = select(ImprovementRecommendation, WeaknessDiagnosis, TextbookTopic, TextbookGroup, Textbook,
        RetrievalChunk, Document).join(WeaknessDiagnosis, WeaknessDiagnosis.id == ImprovementRecommendation.diagnosis_id
        ).join(TextbookTopic, TextbookTopic.id == ImprovementRecommendation.topic_id).join(
        TextbookGroup, TextbookGroup.id == TextbookTopic.group_id).join(Textbook, Textbook.id == TextbookTopic.textbook_id
        ).join(RetrievalChunk, RetrievalChunk.id == ImprovementRecommendation.source_chunk_id).join(
        Document, Document.id == RetrievalChunk.document_id).where(ImprovementRecommendation.topic_id.is_not(None))
    if student_id: topic_query = topic_query.where(ImprovementRecommendation.student_id == student_id)
    if principal.user.role == "student": topic_query = topic_query.where(ImprovementRecommendation.review_status == "approved")
    for r,d,t,g,b,chunk,doc in db.execute(topic_query.order_by(ImprovementRecommendation.created_at.desc())).all():
        recommendations.append(RecommendationResponse(id=r.id, diagnosisId=d.id, studentId=r.student_id,
            subjectId=r.subject_id, topicRef=t.public_ref, topicCode=t.code, topicTitle=t.title,
            groupLabel=b.group_label, groupCode=g.code, groupTitle=g.title, category=d.category,
            description=d.description, observedEvidence=d.evidence.get("items", []), occurrenceCount=d.occurrence_number,
            activityType=r.activity_type, title=r.title, reason=r.reason, action=r.action,
            successCondition=r.success_condition, sourceTitle=doc.title, sourcePage=chunk.page_number,
            sourceUrl=f"/api/v1/retrieval/evidence/{chunk.id}?studentId={r.student_id}",
            questionId=r.activity_question_version_id, reviewStatus=r.review_status,
            reviewReason=r.review_reason, createdAt=r.created_at))
    recommendations.sort(key=lambda item: item.createdAt, reverse=True)
    return RecommendationListResponse(recommendations=recommendations)

def review(db, principal, recommendation_id, payload):
    row = db.get(ImprovementRecommendation, recommendation_id)
    if not row: raise DomainError("recommendation_not_found", "Recommendation not found.", 404)
    if principal.user.role == "parent": _authorize(db, principal, row.student_id)
    row.review_status=payload.decision; row.review_reason=payload.reason; row.reviewed_by=principal.user.id; row.reviewed_at=datetime.now(timezone.utc)
    db.commit()
    return next(item for item in list_recommendations(db, principal, row.student_id).recommendations if item.id == row.id)
