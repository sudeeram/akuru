from __future__ import annotations

import base64
import binascii
import hashlib
import re
import uuid
from pathlib import PurePath
from datetime import datetime, timezone

from sqlalchemy import Text, cast, func, select
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import (
    AssessmentCurriculumSnapshot, AuditEvent, Course, CurriculumPlanTopic, Document, DocumentBlock,
    DocumentJob, DocumentPage, DocumentVersion, ImprovementRecommendation, OfficialQuestionTopicMapping,
    RetrievalChunk, StudyPlanItem, Subject, Textbook, TextbookGroup, TextbookStructureVersion,
    TextbookTopic, TextbookTopicContentSource, TextbookTopicContentVersion, TextbookTopicDocument,
    TopicMastery, WeaknessDiagnosis,
)
from app.schemas.textbook_structures import (
    GroupResponse, GroupSaveRequest, PublishStructureRequest, PublishTopicContentRequest, ReorderRequest,
    TextbookCreateRequest, TextbookListResponse, TextbookResponse, TextbookUpdateRequest,
    TopicReadinessResponse, TopicResponse, TopicSaveRequest,
)
from app.security import Principal
from app.queue import DocumentQueue
from app.storage.base import ObjectStorage
from app.schemas.documents import DocumentType, DocumentUploadResponse, TopicPartBatchRequest, TopicPartSuggestion
from app.services import documents
from app.config import get_settings
from app.services.embeddings import embed_texts


def _book(db: Session, textbook_ref: str, *, include_archived: bool = False) -> Textbook:
    row = db.scalar(select(Textbook).where(Textbook.public_ref == textbook_ref))
    if not row or (row.status == "archived" and not include_archived):
        raise DomainError("textbook_not_found", "The textbook could not be found.", 404)
    return row


def _group(db: Session, book: Textbook, group_ref: str) -> TextbookGroup:
    row = db.scalar(select(TextbookGroup).where(
        TextbookGroup.public_ref == group_ref, TextbookGroup.textbook_id == book.id,
    ))
    if not row:
        raise DomainError("textbook_group_not_found", "The textbook group could not be found.", 404)
    return row


def _topic(db: Session, book: Textbook, topic_ref: str) -> TextbookTopic:
    row = db.scalar(select(TextbookTopic).where(
        TextbookTopic.public_ref == topic_ref, TextbookTopic.textbook_id == book.id,
    ))
    if not row:
        raise DomainError("textbook_topic_not_found", "The textbook topic could not be found.", 404)
    return row


def _topic_references(db: Session, topic_id: uuid.UUID) -> dict[str, int]:
    models = {
        "documents": (TextbookTopicDocument, TextbookTopicDocument.topic_id),
        "coverage": (CurriculumPlanTopic, CurriculumPlanTopic.topic_id),
        "questions": (OfficialQuestionTopicMapping, OfficialQuestionTopicMapping.topic_id),
        "retrieval": (RetrievalChunk, RetrievalChunk.topic_id),
        "mastery": (TopicMastery, TopicMastery.topic_id),
        "weaknesses": (WeaknessDiagnosis, WeaknessDiagnosis.topic_id),
        "recommendations": (ImprovementRecommendation, ImprovementRecommendation.topic_id),
        "studyPlans": (StudyPlanItem, StudyPlanItem.topic_id),
    }
    references = {
        name: int(db.scalar(select(func.count()).select_from(model).where(column == topic_id)) or 0)
        for name, (model, column) in models.items()
    }
    # Assessment snapshots deliberately retain topic UUIDs internally as immutable historical evidence.
    references["assessmentSnapshots"] = int(db.scalar(
        select(func.count()).select_from(AssessmentCurriculumSnapshot).where(
            cast(AssessmentCurriculumSnapshot.covered_topic_ids, Text).contains(str(topic_id)),
        )
    ) or 0)
    return references


def _structure_version(db: Session, textbook_id: uuid.UUID) -> int:
    return int(db.scalar(select(func.max(TextbookStructureVersion.version_number)).where(
        TextbookStructureVersion.textbook_id == textbook_id,
    )) or 0)


def _topic_readiness(db: Session, topic: TextbookTopic) -> TopicReadinessResponse:
    links = db.scalars(select(TextbookTopicDocument).where(TextbookTopicDocument.topic_id == topic.id)).all()
    version = int(db.scalar(select(func.max(TextbookTopicContentVersion.version_number)).where(
        TextbookTopicContentVersion.topic_id == topic.id,
    )) or 0)
    superseded_versions = int(db.scalar(select(func.count()).select_from(TextbookTopicContentVersion).where(
        TextbookTopicContentVersion.topic_id == topic.id,
        TextbookTopicContentVersion.status == "superseded",
    )) or 0)
    statuses = [link.review_status for link in links]
    version_ids = [link.document_version_id for link in links]
    unresolved_pages = int(db.scalar(select(func.count()).select_from(DocumentPage).where(
        DocumentPage.document_version_id.in_(version_ids), DocumentPage.needs_review.is_(True),
    )) or 0) if version_ids else 0
    unresolved_blocks = int(db.scalar(select(func.count()).select_from(DocumentBlock).where(
        DocumentBlock.document_version_id.in_(version_ids), DocumentBlock.needs_review.is_(True),
    )) or 0) if version_ids else 0
    average = float(db.scalar(select(func.avg(DocumentBlock.confidence)).where(
        DocumentBlock.document_version_id.in_(version_ids),
    )) or 0) if version_ids else 0
    primary = sum(link.role == "primary" for link in links)
    processing = sum(value in {"pending", "processing"} for value in statuses)
    review = sum(value == "needs_review" for value in statuses)
    failed = sum(value == "failed" for value in statuses)
    source_ready = bool(primary) and all(value in {"ready", "published"} for value in statuses)
    published = db.scalar(select(TextbookTopicContentVersion).where(
        TextbookTopicContentVersion.topic_id == topic.id, TextbookTopicContentVersion.status == "published",
    ))
    live_fingerprints = []
    for link in links:
        job = db.scalar(select(DocumentJob).where(
            DocumentJob.document_version_id == link.document_version_id,
            DocumentJob.status.in_(("completed", "needs_review")),
        ).order_by(DocumentJob.completed_at.desc().nullslast()))
        blocks = db.scalars(select(DocumentBlock).where(
            DocumentBlock.document_version_id == link.document_version_id,
        ).order_by(DocumentBlock.page_id, DocumentBlock.sequence_number)).all()
        digest = hashlib.sha256("\n".join(
            f"{block.id}:{block.sequence_number}:{block.block_kind}:{block.text}:{block.latex or ''}"
            for block in blocks).encode()).hexdigest()
        live_fingerprints.append({"documentVersionId": str(link.document_version_id), "role": link.role,
                                  "sequence": link.sequence,
                                  "extractionVersion": job.extraction_version if job else "",
                                  "reviewedContentHash": digest})
    published_fingerprints = [{key: row.get(key) for key in (
        "documentVersionId", "role", "sequence", "extractionVersion", "reviewedContentHash"
    )} for row in (published.source_manifest if published else [])]
    has_draft_changes = not published or live_fingerprints != published_fingerprints
    ready = source_ready and not unresolved_pages and not unresolved_blocks and has_draft_changes
    if published: state = "published"
    elif not links: state = "no_document"
    elif failed: state = "failed"
    elif processing: state = "processing"
    elif review or unresolved_pages or unresolved_blocks: state = "needs_review"
    elif ready: state = "ready"
    else: state = "needs_review"
    checks = [
        {"code": "primary_source", "passed": primary > 0, "message": "At least one primary textbook part is required."},
        {"code": "processing_complete", "passed": processing == 0, "message": "All processing jobs must finish."},
        {"code": "extraction_review", "passed": review == 0 and unresolved_pages == 0 and unresolved_blocks == 0,
         "message": "Every flagged page and block must be reviewed."},
        {"code": "no_failures", "passed": failed == 0, "message": "Failed textbook parts must be retried or removed."},
        {"code": "new_version", "passed": has_draft_changes,
         "message": "A published topic needs reviewed changes before another version is created."},
    ]
    return TopicReadinessResponse(state=state, ready=ready, contentVersion=version,
        supersededVersionCount=superseded_versions,
        hasDraftChanges=has_draft_changes,
        documentCount=len(links), primaryDocumentCount=primary, processingCount=processing,
        needsReviewCount=review, failedCount=failed, unresolvedPageCount=unresolved_pages,
        unresolvedBlockCount=unresolved_blocks, averageConfidence=round(average, 4), checks=checks)


def _response(db: Session, book: Textbook) -> TextbookResponse:
    groups = db.scalars(select(TextbookGroup).where(
        TextbookGroup.textbook_id == book.id, TextbookGroup.status != "archived",
    ).order_by(TextbookGroup.sequence, TextbookGroup.code)).all()
    group_responses = []
    for group in groups:
        topics = db.scalars(select(TextbookTopic).where(
            TextbookTopic.group_id == group.id, TextbookTopic.status != "archived",
        ).order_by(TextbookTopic.sequence, TextbookTopic.code)).all()
        topic_responses = []
        for topic in topics:
            references = _topic_references(db, topic.id)
            topic_responses.append(TopicResponse(
                topicRef=topic.public_ref, code=topic.code, title=topic.title, sequence=topic.sequence,
                syllabusRef=topic.syllabus_ref, description=topic.description, status=topic.status,
                documentCount=references["documents"], removable=not any(references.values()),
                content=_topic_readiness(db, topic),
            ))
        group_responses.append(GroupResponse(
            groupRef=group.public_ref, code=group.code, title=group.title, summary=group.summary,
            sequence=group.sequence, status=group.status, topics=topic_responses,
            removable=not topics,
        ))
    return TextbookResponse(
        textbookRef=book.public_ref, courseId=book.course_id, subjectId=book.subject_id,
        title=book.title, edition=book.edition, publisher=book.publisher,
        groupLabel=book.group_label, groupDisplayLabel="Unit" if book.group_label == "unit" else "Module",
        status=book.status, structureVersion=_structure_version(db, book.id), groups=group_responses,
    )


def _audit(db: Session, principal: Principal, action: str, target_type: str, target_id: str, data: dict) -> None:
    db.add(AuditEvent(actor_id=principal.user.id, action=action, target_type=target_type,
                      target_id=target_id, event_data=data))


def _mark_draft(book: Textbook) -> None:
    if book.status == "published":
        book.status = "draft"
        book.published_by = None
        book.published_at = None


def list_textbooks(db: Session) -> TextbookListResponse:
    rows = db.scalars(select(Textbook).where(Textbook.status != "archived").order_by(
        Textbook.subject_id, Textbook.title, Textbook.edition,
    )).all()
    return TextbookListResponse(textbooks=[_response(db, row) for row in rows])


def get_textbook(db: Session, textbook_ref: str) -> TextbookResponse:
    return _response(db, _book(db, textbook_ref))


def create_textbook(db: Session, principal: Principal, payload: TextbookCreateRequest) -> TextbookResponse:
    course = db.get(Course, payload.courseId)
    if not course or not course.phase1_active:
        raise DomainError("inactive_course", "Only the active iGCSE course can receive textbooks.", 422)
    if not db.get(Subject, payload.subjectId):
        raise DomainError("subject_not_found", "Choose a supported iGCSE subject.", 422)
    duplicate = db.scalar(select(Textbook).where(
        Textbook.course_id == payload.courseId, Textbook.subject_id == payload.subjectId,
        func.lower(Textbook.title) == payload.title.lower(), func.lower(Textbook.edition) == payload.edition.lower(),
    ))
    if duplicate:
        raise DomainError("duplicate_textbook_edition", "This textbook edition already exists.", 409)
    row = Textbook(course_id=payload.courseId, subject_id=payload.subjectId, title=payload.title,
                   edition=payload.edition, publisher=payload.publisher, group_label=payload.groupLabel,
                   created_by=principal.user.id)
    db.add(row); db.flush()
    _audit(db, principal, "textbook.created", "textbook", row.public_ref,
           {"subjectId": row.subject_id, "groupLabel": row.group_label})
    db.commit(); db.refresh(row)
    return _response(db, row)


def update_textbook(db: Session, principal: Principal, textbook_ref: str, payload: TextbookUpdateRequest) -> TextbookResponse:
    row = _book(db, textbook_ref)
    duplicate = db.scalar(select(Textbook).where(
        Textbook.id != row.id, Textbook.course_id == row.course_id, Textbook.subject_id == row.subject_id,
        func.lower(Textbook.title) == payload.title.lower(), func.lower(Textbook.edition) == payload.edition.lower(),
    ))
    if duplicate:
        raise DomainError("duplicate_textbook_edition", "This textbook edition already exists.", 409)
    before = {"title": row.title, "edition": row.edition, "publisher": row.publisher, "groupLabel": row.group_label}
    _mark_draft(row)
    row.title, row.edition, row.publisher, row.group_label = payload.title, payload.edition, payload.publisher, payload.groupLabel
    _audit(db, principal, "textbook.updated", "textbook", row.public_ref, {"before": before})
    db.commit(); db.refresh(row)
    return _response(db, row)


def archive_textbook(db: Session, principal: Principal, textbook_ref: str) -> TextbookResponse:
    row = _book(db, textbook_ref)
    row.status = "archived"; row.archived_at = datetime.now(timezone.utc)
    _audit(db, principal, "textbook.archived", "textbook", row.public_ref, {})
    db.commit(); db.refresh(row)
    return _response(db, row)


def save_group(db: Session, principal: Principal, textbook_ref: str, payload: GroupSaveRequest,
               group_ref: str | None = None) -> TextbookResponse:
    book = _book(db, textbook_ref)
    row = _group(db, book, group_ref) if group_ref else TextbookGroup(textbook_id=book.id)
    duplicate = db.scalar(select(TextbookGroup).where(
        TextbookGroup.textbook_id == book.id, TextbookGroup.id != row.id,
        ((func.lower(TextbookGroup.code) == payload.code.lower()) | (TextbookGroup.sequence == payload.sequence)),
        TextbookGroup.status != "archived",
    ))
    if duplicate:
        raise DomainError("duplicate_textbook_group", "Group code and order must be unique within the textbook.", 409)
    _mark_draft(book)
    row.code, row.title, row.summary, row.sequence, row.status = payload.code, payload.title, payload.summary, payload.sequence, "draft"
    db.add(row); db.flush()
    _audit(db, principal, "textbook_group.saved", "textbook_group", row.public_ref, {"textbookRef": book.public_ref})
    db.commit()
    return _response(db, book)


def remove_group(db: Session, principal: Principal, textbook_ref: str, group_ref: str) -> TextbookResponse:
    book = _book(db, textbook_ref); row = _group(db, book, group_ref)
    topics = db.scalar(select(func.count()).select_from(TextbookTopic).where(
        TextbookTopic.group_id == row.id, TextbookTopic.status != "archived",
    )) or 0
    if topics:
        raise DomainError("textbook_group_not_empty", "Remove or archive this group's topics first.", 409)
    _mark_draft(book)
    db.delete(row)
    _audit(db, principal, "textbook_group.removed", "textbook_group", row.public_ref, {"archived": False})
    db.commit()
    return _response(db, book)


def reorder_groups(db: Session, principal: Principal, textbook_ref: str, payload: ReorderRequest) -> TextbookResponse:
    book = _book(db, textbook_ref)
    rows = db.scalars(select(TextbookGroup).where(
        TextbookGroup.textbook_id == book.id, TextbookGroup.status != "archived",
    )).all()
    if set(payload.refs) != {row.public_ref for row in rows}:
        raise DomainError("invalid_group_order", "Include every active group exactly once.", 422)
    _mark_draft(book)
    # Move through a disjoint temporary range so database uniqueness remains valid while swapping rows.
    for offset, row in enumerate(rows, 1):
        row.sequence = 10_000 + offset
    db.flush()
    for sequence, ref in enumerate(payload.refs, 1):
        next(row for row in rows if row.public_ref == ref).sequence = sequence
    _audit(db, principal, "textbook_groups.reordered", "textbook", book.public_ref, {"groupRefs": payload.refs})
    db.commit()
    return _response(db, book)


def save_topic(db: Session, principal: Principal, textbook_ref: str, group_ref: str, payload: TopicSaveRequest,
               topic_ref: str | None = None) -> TextbookResponse:
    book = _book(db, textbook_ref); group = _group(db, book, group_ref)
    row = _topic(db, book, topic_ref) if topic_ref else TextbookTopic(
        textbook_id=book.id, group_id=group.id, course_id=book.course_id, subject_id=book.subject_id,
    )
    if topic_ref and row.group_id != group.id:
        raise DomainError("topic_group_mismatch", "The topic does not belong to this group.", 409)
    code_duplicate = db.scalar(select(TextbookTopic).where(
        TextbookTopic.textbook_id == book.id, TextbookTopic.id != row.id,
        func.lower(TextbookTopic.code) == payload.code.lower(), TextbookTopic.status != "archived",
    ))
    order_duplicate = db.scalar(select(TextbookTopic).where(
        TextbookTopic.group_id == group.id, TextbookTopic.id != row.id,
        TextbookTopic.sequence == payload.sequence, TextbookTopic.status != "archived",
    ))
    if code_duplicate or order_duplicate:
        raise DomainError("duplicate_textbook_topic", "Topic code must be unique in the textbook and order unique in its group.", 409)
    _mark_draft(book)
    row.code, row.title, row.sequence = payload.code, payload.title, payload.sequence
    row.syllabus_ref, row.description, row.status = payload.syllabusRef, payload.description, "draft"
    db.add(row); db.flush()
    _audit(db, principal, "textbook_topic.saved", "textbook_topic", row.public_ref,
           {"textbookRef": book.public_ref, "groupRef": group.public_ref})
    db.commit()
    return _response(db, book)


def remove_topic(db: Session, principal: Principal, textbook_ref: str, topic_ref: str) -> TextbookResponse:
    book = _book(db, textbook_ref); row = _topic(db, book, topic_ref)
    references = _topic_references(db, row.id)
    if any(references.values()):
        raise DomainError("textbook_topic_in_use", "This topic is referenced and cannot be removed.", 409,
                          [{"references": references}])
    _mark_draft(book)
    db.delete(row)
    _audit(db, principal, "textbook_topic.removed", "textbook_topic", row.public_ref, {"archived": False})
    db.commit()
    return _response(db, book)


def reorder_topics(db: Session, principal: Principal, textbook_ref: str, group_ref: str,
                   payload: ReorderRequest) -> TextbookResponse:
    book = _book(db, textbook_ref); group = _group(db, book, group_ref)
    rows = db.scalars(select(TextbookTopic).where(
        TextbookTopic.group_id == group.id, TextbookTopic.status != "archived",
    )).all()
    if set(payload.refs) != {row.public_ref for row in rows}:
        raise DomainError("invalid_topic_order", "Include every active topic in this group exactly once.", 422)
    _mark_draft(book)
    for offset, row in enumerate(rows, 1):
        row.sequence = 10_000 + offset
    db.flush()
    for sequence, ref in enumerate(payload.refs, 1):
        next(row for row in rows if row.public_ref == ref).sequence = sequence
    _audit(db, principal, "textbook_topics.reordered", "textbook_group", group.public_ref, {"topicRefs": payload.refs})
    db.commit()
    return _response(db, book)


def publish_structure(db: Session, principal: Principal, textbook_ref: str,
                      confirmation: PublishStructureRequest) -> TextbookResponse:
    book = _book(db, textbook_ref)
    if not all((confirmation.confirmCourse, confirmation.confirmSubject,
                confirmation.confirmEdition, confirmation.confirmStructure)):
        raise DomainError("textbook_structure_confirmation_required", "Confirm the textbook identity and complete structure.", 422)
    groups = db.scalars(select(TextbookGroup).where(
        TextbookGroup.textbook_id == book.id, TextbookGroup.status != "archived",
    ).order_by(TextbookGroup.sequence)).all()
    if not groups:
        raise DomainError("textbook_groups_required", "Add at least one Unit or Module before publishing.", 409)
    snapshot_groups = []
    for group in groups:
        topics = db.scalars(select(TextbookTopic).where(
            TextbookTopic.group_id == group.id, TextbookTopic.status != "archived",
        ).order_by(TextbookTopic.sequence)).all()
        if not topics:
            raise DomainError("textbook_topics_required", f"{group.code} must contain at least one topic.", 409)
        snapshot_groups.append({"groupRef": group.public_ref, "code": group.code, "title": group.title,
                                "summary": group.summary, "sequence": group.sequence,
                                "topics": [{"topicRef": topic.public_ref, "code": topic.code, "title": topic.title,
                                            "sequence": topic.sequence, "syllabusRef": topic.syllabus_ref,
                                            "description": topic.description} for topic in topics]})
        group.status = "published"
        for topic in topics: topic.status = "published"
    version = _structure_version(db, book.id) + 1
    now = datetime.now(timezone.utc)
    db.add(TextbookStructureVersion(textbook_id=book.id, version_number=version,
                                    snapshot={"textbookRef": book.public_ref, "courseId": book.course_id,
                                              "subjectId": book.subject_id, "title": book.title,
                                              "edition": book.edition, "publisher": book.publisher,
                                              "groupLabel": book.group_label, "groups": snapshot_groups},
                                    published_by=principal.user.id, published_at=now))
    book.status = "published"; book.published_by = principal.user.id; book.published_at = now
    _audit(db, principal, "textbook_structure.published", "textbook", book.public_ref,
           {"versionNumber": version, "groupCount": len(groups),
            "topicCount": sum(len(group["topics"]) for group in snapshot_groups)})
    db.commit(); db.refresh(book)
    return _response(db, book)


def upload_topic_part(db: Session, storage: ObjectStorage, queue: DocumentQueue, principal: Principal,
                      textbook_ref: str, topic_ref: str, *, content: bytes, filename: str,
                      content_type: str, role: str, printed_start_page: str | None,
                      printed_end_page: str | None, idempotency_key: str) -> DocumentUploadResponse:
    book = _book(db, textbook_ref); topic = _topic(db, book, topic_ref)
    if role not in {"primary", "supporting", "reference"}:
        raise DomainError("invalid_topic_document_role", "Choose primary, supporting or reference.", 422)
    scoped_key = f"topic-part:{topic.public_ref}:{idempotency_key.strip()}"
    response = documents.upload_document(
        db, storage, queue, principal, content=content, filename=filename, content_type=content_type,
        kind=DocumentType.TEXTBOOK, course_id=book.course_id, subject_id=book.subject_id,
        title=PurePath(filename).stem, edition=book.edition, publication_year=None,
        exam_session=None, component=None, variant=None, source_document_id=None,
        publisher=book.publisher, isbn=None, source_url=None, upload_request_key=scoped_key,
        extra_metadata={"textbookRef": book.public_ref, "groupRef": db.get(TextbookGroup, topic.group_id).public_ref,
                        "topicRef": topic.public_ref, "documentRole": role},
    )
    version_id = uuid.UUID(response.document.versionId)
    existing = db.scalar(select(TextbookTopicDocument).where(
        TextbookTopicDocument.topic_id == topic.id, TextbookTopicDocument.document_version_id == version_id,
    ))
    if not existing:
        sequence = int(db.scalar(select(func.max(TextbookTopicDocument.sequence)).where(
            TextbookTopicDocument.topic_id == topic.id,
        )) or 0) + 1
        db.add(TextbookTopicDocument(
            topic_id=topic.id, document_version_id=version_id,
            document_id=uuid.UUID(response.document.id), role=role, sequence=sequence,
            printed_start_page=(printed_start_page or "").strip() or None,
            printed_end_page=(printed_end_page or "").strip() or None,
            review_status="processing", created_by=principal.user.id,
        ))
        _audit(db, principal, "textbook_topic_document.attached", "textbook_topic", topic.public_ref,
               {"textbookRef": book.public_ref, "documentId": response.document.id, "role": role})
        db.commit()
    return response


def upload_topic_parts_batch(db: Session, storage: ObjectStorage, queue: DocumentQueue,
                             principal: Principal, textbook_ref: str, topic_ref: str,
                             payload: TopicPartBatchRequest) -> list[DocumentUploadResponse]:
    decoded = []
    for item in payload.items:
        try:
            content = base64.b64decode(item.contentBase64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise DomainError("invalid_base64_document", f"{item.filename} is not valid encoded file data.", 422) from exc
        decoded.append((item, content))
    if sum(len(content) for _, content in decoded) > documents.settings.max_document_bytes * 5:
        raise DomainError("batch_too_large", "The batch exceeds the five-document upload size limit.", 413)
    return [upload_topic_part(
        db, storage, queue, principal, textbook_ref, topic_ref, content=content,
        filename=item.filename, content_type=item.contentType, role=item.role,
        printed_start_page=item.printedStartPage, printed_end_page=item.printedEndPage,
        idempotency_key=item.idempotencyKey,
    ) for item, content in decoded]


def suggest_topics(db: Session, textbook_ref: str, filenames: list[str]) -> list[TopicPartSuggestion]:
    book = _book(db, textbook_ref)
    topics = db.scalars(select(TextbookTopic).where(
        TextbookTopic.textbook_id == book.id, TextbookTopic.status != "archived",
    )).all()
    suggestions = []
    for filename in filenames:
        normalized = re.sub(r"[^a-z0-9]+", " ", PurePath(filename).stem.lower()).strip()
        ranked = []
        for topic in topics:
            code = re.sub(r"[^a-z0-9]+", " ", topic.code.lower()).strip()
            title = re.sub(r"[^a-z0-9]+", " ", topic.title.lower()).strip()
            score = 1.0 if code and re.search(rf"(?:^| ){re.escape(code)}(?: |$)", normalized) else (
                0.8 if title and title in normalized else 0.0)
            ranked.append((score, topic))
        score, topic = max(ranked, key=lambda row: row[0], default=(0.0, None))
        suggestions.append(TopicPartSuggestion(filename=filename,
            suggestedTopicRef=topic.public_ref if topic and score else None,
            suggestedTopicCode=topic.code if topic and score else None, confidence=score))
    return suggestions


def publish_topic_content(db: Session, principal: Principal, textbook_ref: str, topic_ref: str,
                          confirmation: PublishTopicContentRequest) -> TextbookResponse:
    if not all((confirmation.confirmSources, confirmation.confirmExtraction, confirmation.confirmTopic)):
        raise DomainError("topic_publication_confirmation_required",
                          "Confirm the topic, reviewed sources and extraction before publishing.", 422)
    book = _book(db, textbook_ref); topic = _topic(db, book, topic_ref)
    readiness = _topic_readiness(db, topic)
    if not readiness.ready:
        raise DomainError("topic_content_not_ready", "Resolve every topic readiness check before publishing.", 409,
                          [check for check in readiness.checks if not check["passed"]])
    links = db.scalars(select(TextbookTopicDocument).where(
        TextbookTopicDocument.topic_id == topic.id,
        TextbookTopicDocument.review_status.in_(("ready", "published")),
    ).order_by(TextbookTopicDocument.sequence).with_for_update()).all()
    source_manifest = []
    blocks_to_index = []
    for link in links:
        document = db.get(Document, link.document_id); version = db.get(DocumentVersion, link.document_version_id)
        job = db.scalar(select(DocumentJob).where(DocumentJob.document_version_id == version.id,
                                                   DocumentJob.status.in_(("completed", "needs_review"))).order_by(
            DocumentJob.completed_at.desc().nullslast()))
        if not document or not version or not job:
            raise DomainError("topic_source_unavailable", "A reviewed topic source is unavailable.", 409)
        pages = db.scalars(select(DocumentPage).where(DocumentPage.document_version_id == version.id)).all()
        blocks = db.scalars(select(DocumentBlock).where(
            DocumentBlock.document_version_id == version.id, DocumentBlock.needs_review.is_(False),
        ).order_by(DocumentBlock.page_id, DocumentBlock.sequence_number)).all()
        page_map = {page.id: page for page in pages}
        digest = hashlib.sha256("\n".join(
            f"{block.id}:{block.sequence_number}:{block.block_kind}:{block.text}:{block.latex or ''}"
            for block in blocks).encode()).hexdigest()
        source_manifest.append({"documentId": str(document.id), "documentVersionId": str(version.id),
                                "documentVersion": version.version_number, "checksum": version.sha256,
                                "role": link.role, "sequence": link.sequence,
                                "extractionVersion": job.extraction_version, "reviewedContentHash": digest})
        for block in blocks:
            page = page_map.get(block.page_id)
            if page and (block.text.strip() or block.latex):
                blocks_to_index.append((document, version, page, block))
    if not blocks_to_index:
        raise DomainError("topic_content_empty", "The reviewed sources contain no publishable text or formulae.", 409)
    prior = db.scalar(select(TextbookTopicContentVersion).where(
        TextbookTopicContentVersion.topic_id == topic.id,
        TextbookTopicContentVersion.status == "published",
    ).with_for_update())
    now = datetime.now(timezone.utc)
    next_version = (prior.version_number + 1) if prior else 1
    if prior:
        prior.status = "superseded"; prior.superseded_at = now
        db.execute(RetrievalChunk.__table__.update().where(
            RetrievalChunk.topic_content_version_id == prior.id, RetrievalChunk.status == "active",
        ).values(status="superseded", superseded_at=now))
    content_version = TextbookTopicContentVersion(
        topic_id=topic.id, version_number=next_version, status="published", source_manifest=source_manifest,
        extraction_manifest={"blockCount": len(blocks_to_index), "averageConfidence": readiness.averageConfidence,
                             "unresolvedPageCount": 0, "unresolvedBlockCount": 0},
        published_by=principal.user.id, published_at=now,
    )
    db.add(content_version); db.flush()
    for link, manifest in zip(links, source_manifest):
        db.add(TextbookTopicContentSource(content_version_id=content_version.id,
            document_version_id=link.document_version_id, role=link.role,
            extraction_version=manifest["extractionVersion"]))
        link.review_status = "published"
        document = db.get(Document, link.document_id)
        if document: document.review_state = "published"
    settings = get_settings(); embeddings = embed_texts(settings, [block.text or block.latex or "" for _, _, _, block in blocks_to_index])
    for ordinal, ((document, version, page, block), embedding) in enumerate(zip(blocks_to_index, embeddings), 1):
        content = block.text.strip() or block.latex or ""
        db.add(RetrievalChunk(document_id=document.id, document_version_id=version.id,
            textbook_content_version_id=None, official_material_version_id=None, unit_id=None,
            group_id=topic.group_id, topic_id=topic.id, topic_content_version_id=content_version.id,
            course_id=topic.course_id, subject_id=topic.subject_id, source_type="textbook_section",
            source_item_id=block.id, source_ordinal=ordinal, content=content, page_number=page.page_number,
            bounding_box=block.bounding_box, source_asset_id=block.source_asset_id or page.render_asset_id,
            content_hash=hashlib.sha256(content.encode()).hexdigest(), embedding_model=settings.embedding_model,
            embedding_version=next_version, embedding=embedding, status="active"))
    _audit(db, principal, "textbook_topic_content.published", "textbook_topic", topic.public_ref,
           {"textbookRef": book.public_ref, "contentVersion": next_version,
            "sourceCount": len(links), "chunkCount": len(blocks_to_index)})
    db.commit()
    return _response(db, book)
