"""Explicitly released subject references, including the Pearson specification."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import AuditEvent, Document, DocumentVersion, StudentSubject
from app.security import Principal
from app.storage.base import ObjectStorage, StoredObject
from app.services.documents import final_document


def _latest(db: Session, document_id: uuid.UUID) -> DocumentVersion | None:
    return db.scalar(select(DocumentVersion).where(
        DocumentVersion.document_id == document_id,
        DocumentVersion.status != "removed",
    ).order_by(DocumentVersion.version_number.desc()))


def publish(db: Session, principal: Principal, document_id: uuid.UUID) -> dict:
    document = db.get(Document, document_id)
    version = _latest(db, document_id)
    if not document or document.removed_at or document.kind != "reference" or not version:
        raise DomainError("reference_not_found", "Reference material not found.", 404)
    if document.review_state != "reviewed" or version.status != "completed":
        raise DomainError("reference_review_required", "Review the reference PDF before publishing it.", 409)
    reviewed = final_document(db, document_id)
    if reviewed.blockers or not reviewed.confirmed or reviewed.versionId != str(version.id):
        raise DomainError("reference_final_review_required", "Confirm the final reviewed document before publishing it.", 409)
    if version.mime_type != "application/pdf":
        raise DomainError("reference_pdf_required", "Student references must be PDF files.", 409)
    document.source_metadata = {**(document.source_metadata or {}), "publishedReferenceVersionId": str(version.id)}
    document.review_state = "published"
    db.add(AuditEvent(actor_id=principal.user.id, action="reference.published",
                      target_type="document", target_id=str(document.id),
                      event_data={"versionId": str(version.id), "contentHash": document.source_metadata["finalDocumentReview"]["contentHash"]}))
    db.commit()
    return {"id": str(document.id), "status": "published"}


def _available(db: Session, principal: Principal, document_id: uuid.UUID) -> tuple[Document, DocumentVersion]:
    document = db.get(Document, document_id)
    if not document or document.kind != "reference" or document.review_state != "published" or document.removed_at:
        raise DomainError("reference_not_available", "Reference material is unavailable.", 404)
    if document.course_id != "igcse" or not db.get(StudentSubject, (principal.user.id, document.subject_id)):
        raise DomainError("reference_not_available", "Reference material is unavailable.", 404)
    version_id = (document.source_metadata or {}).get("publishedReferenceVersionId")
    try:
        version = db.get(DocumentVersion, uuid.UUID(version_id)) if version_id else None
    except (ValueError, TypeError):
        version = None
    if not version or version.document_id != document.id or version.status != "completed" or version.mime_type != "application/pdf":
        raise DomainError("reference_not_available", "Reference material is unavailable.", 404)
    return document, version


def list_for_student(db: Session, principal: Principal) -> list[dict]:
    subject_ids = list(db.scalars(select(StudentSubject.subject_id).where(
        StudentSubject.student_id == principal.user.id)).all())
    if not subject_ids:
        return []
    documents = db.scalars(select(Document).where(
        Document.kind == "reference", Document.review_state == "published",
        Document.removed_at.is_(None), Document.course_id == "igcse",
        Document.subject_id.in_(subject_ids)).order_by(Document.subject_id, Document.title)).all()
    result = []
    for document in documents:
        try:
            _, version = _available(db, principal, document.id)
        except DomainError:
            continue
        if version:
            result.append({"id": str(document.id), "subjectId": document.subject_id,
                           "title": document.title, "filename": version.original_filename,
                           "publicationYear": document.publication_year,
                           "contentUrl": f"/api/v1/student/references/{document.id}/content"})
    return result


def content(db: Session, storage: ObjectStorage, principal: Principal, document_id: uuid.UUID) -> StoredObject:
    _document, version = _available(db, principal, document_id)
    return storage.get(version.object_key, version.mime_type)
