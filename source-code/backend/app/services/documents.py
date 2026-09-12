from __future__ import annotations

import hashlib
import uuid
from pathlib import PurePath

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import DomainError
from app.models import Document, DocumentJob, DocumentVersion
from app.queue import DocumentQueue
from app.repositories.documents import DocumentRepository
from app.schemas.documents import DocumentResponse, DocumentType, DocumentUploadResponse
from app.security import Principal, utcnow
from app.services.document_processing import enqueue_safely, job_response
from app.storage.base import ObjectStorage, StoredObject


settings = get_settings()
FILE_TYPES = {
    ".pdf": ("application/pdf", lambda data: data.startswith(b"%PDF-")),
    ".png": ("image/png", lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
    ".jpg": ("image/jpeg", lambda data: data.startswith(b"\xff\xd8\xff")),
    ".jpeg": ("image/jpeg", lambda data: data.startswith(b"\xff\xd8\xff")),
}


def validate_file(filename: str, content_type: str, content: bytes) -> str:
    if not filename or filename != PurePath(filename).name or any(char in filename for char in ("/", "\\", "\r", "\n")):
        raise DomainError("invalid_filename", "Choose a file with a valid name.", 422)
    if len(filename) > 255:
        raise DomainError("invalid_filename", "The filename must be 255 characters or fewer.", 422)
    if not content:
        raise DomainError("empty_document", "The uploaded document is empty.", 422)
    if len(content) > settings.max_document_bytes:
        raise DomainError(
            "document_too_large",
            f"The document exceeds the {settings.max_document_bytes // (1024 * 1024)} MB limit.",
            413,
        )
    extension = PurePath(filename).suffix.lower()
    expected = FILE_TYPES.get(extension)
    if not expected:
        raise DomainError("unsupported_file_type", "Upload a PDF, PNG or JPEG file.", 422)
    expected_mime, signature_matches = expected
    normalized_mime = content_type.split(";", 1)[0].strip().lower()
    if normalized_mime != expected_mime:
        raise DomainError(
            "content_type_mismatch",
            f"The file extension does not match its content type; expected {expected_mime}.",
            422,
        )
    if not signature_matches(content):
        raise DomainError(
            "file_signature_mismatch",
            "The file contents do not match the selected file type.",
            422,
        )
    return normalized_mime


def _validate_relationships(
    repository: DocumentRepository,
    kind: DocumentType,
    course_id: str,
    subject_id: str,
    source_document_id: uuid.UUID | None,
) -> None:
    if not repository.course_and_subject_exist(course_id, subject_id):
        raise DomainError("invalid_document_scope", "Choose an active course and valid subject.", 422)
    if kind == DocumentType.PAST_PAPER and not repository.has_textbook(course_id, subject_id):
        raise DomainError(
            "textbook_required",
            "Upload a textbook for this course and subject before uploading a past paper.",
            409,
        )
    if kind in (DocumentType.MARK_SCHEME, DocumentType.EXAMINER_REPORT):
        if source_document_id is None:
            raise DomainError("source_paper_required", "Choose the related past paper.", 422)
        paper = repository.source_paper(source_document_id)
        if not paper or paper.course_id != course_id or paper.subject_id != subject_id:
            raise DomainError(
                "invalid_source_paper",
                "Choose a past paper from the same course and subject.",
                422,
            )


def upload_document(
    db: Session,
    storage: ObjectStorage,
    queue: DocumentQueue,
    principal: Principal,
    *,
    content: bytes,
    filename: str,
    content_type: str,
    kind: DocumentType,
    course_id: str,
    subject_id: str,
    title: str,
    edition: str | None,
    publication_year: int | None,
    exam_session: str | None,
    component: str | None,
    variant: str | None,
    source_document_id: uuid.UUID | None,
    publisher: str | None,
    isbn: str | None,
    source_url: str | None,
) -> DocumentUploadResponse:
    normalized_mime = validate_file(filename, content_type, content)
    title = title.strip()
    if not title:
        raise DomainError("title_required", "Document title is required.", 422)
    repository = DocumentRepository(db)
    _validate_relationships(repository, kind, course_id, subject_id, source_document_id)
    checksum = hashlib.sha256(content).hexdigest()
    if repository.checksum_exists(checksum):
        raise DomainError("duplicate_document", "This exact file has already been uploaded.", 409)

    document_id = uuid.uuid4()
    version_id = uuid.uuid4()
    extension = PurePath(filename).suffix.lower()
    object_key = f"documents/{document_id}/versions/{version_id}/original{extension}"
    metadata = {
        key: value for key, value in {
            "publisher": publisher,
            "isbn": isbn,
            "sourceUrl": source_url,
        }.items() if value
    }
    storage.put(object_key, content, normalized_mime)
    document = Document(
        id=document_id,
        kind=kind.value,
        course_id=course_id,
        subject_id=subject_id,
        title=title,
        original_filename=filename,
        object_key=object_key,
        mime_type=normalized_mime,
        sha256=checksum,
        review_state="pending",
        uploaded_by=principal.user.id,
        source_document_id=source_document_id,
        edition=edition,
        publication_year=publication_year,
        exam_session=exam_session,
        component=component,
        variant=variant,
        source_metadata=metadata,
        size_bytes=len(content),
    )
    version = DocumentVersion(
        id=version_id,
        document_id=document_id,
        version_number=1,
        original_filename=filename,
        object_key=object_key,
        mime_type=normalized_mime,
        sha256=checksum,
        size_bytes=len(content),
        status="queued",
        uploaded_by=principal.user.id,
    )
    job = DocumentJob(
        document_id=document_id,
        document_version_id=version_id,
        stage="preflight",
        status="queued",
        progress=0,
        extraction_version=settings.extraction_version,
        max_seconds=settings.document_job_timeout_seconds,
        max_memory_mb=settings.document_job_memory_mb,
        max_pages=settings.document_max_pages,
    )
    db.add_all((document, version))
    try:
        db.flush()
        db.add(job)
        db.flush()
        repository.add_event(
            document, version, principal.user.id, "queued",
            {"sha256": checksum, "jobId": str(job.id)},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        storage.delete(object_key)
        constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", "")
        if constraint in {"documents_sha256_key", "document_versions_sha256_key"}:
            raise DomainError("duplicate_document", "This exact file has already been uploaded.", 409) from exc
        raise DomainError(
            "document_storage_conflict",
            "The document metadata conflicts with an existing record.",
            409,
        ) from exc
    db.refresh(document)
    db.refresh(version)
    db.refresh(job)
    enqueue_safely(db, queue, job, repository, principal.user.id)
    return DocumentUploadResponse(document=document_response(document, version), job=job_response(job))


def document_response(document: Document, version: DocumentVersion) -> DocumentResponse:
    return DocumentResponse(
        id=str(document.id),
        kind=document.kind,
        courseId=document.course_id,
        subjectId=document.subject_id,
        title=document.title,
        originalFilename=version.original_filename,
        contentType=version.mime_type,
        sizeBytes=version.size_bytes,
        checksum=version.sha256,
        status="removed" if document.removed_at else version.status,
        edition=document.edition,
        year=document.publication_year,
        session=document.exam_session,
        component=document.component,
        variant=document.variant,
        sourceDocumentId=str(document.source_document_id) if document.source_document_id else None,
        sourceMetadata=document.source_metadata,
        versionId=str(version.id),
        versionNumber=version.version_number,
        createdAt=document.created_at,
        removedAt=document.removed_at,
    )


def list_documents(db: Session) -> list[DocumentResponse]:
    return [document_response(document, version) for document, version in DocumentRepository(db).active_documents()]


def get_document(db: Session, document_id: uuid.UUID) -> tuple[Document, DocumentVersion]:
    repository = DocumentRepository(db)
    document = repository.document(document_id)
    if not document or document.removed_at:
        raise DomainError("document_not_found", "Document not found.", 404)
    version = repository.latest_version(document_id)
    if not version:
        raise DomainError("document_version_not_found", "Document version not found.", 404)
    return document, version


def download_document(db: Session, storage: ObjectStorage, document_id: uuid.UUID) -> StoredObject:
    _document, version = get_document(db, document_id)
    try:
        return storage.get(version.object_key, version.mime_type)
    except FileNotFoundError as exc:
        raise DomainError("document_bytes_missing", "The stored document could not be found.", 500) from exc


def remove_document(db: Session, principal: Principal, document_id: uuid.UUID) -> None:
    document, version = get_document(db, document_id)
    document.removed_at = utcnow()
    version.status = "removed"
    repository = DocumentRepository(db)
    job = repository.latest_job(document_id)
    if job and job.status in {"queued", "processing"}:
        job.status = "failed"
        job.progress = 100
        job.error_code = "document_removed"
        job.error_message = "The document was removed before processing completed."
        job.completed_at = utcnow()
    repository.add_event(document, version, principal.user.id, "removed")
    db.commit()
