from __future__ import annotations

import hashlib
import uuid
from pathlib import PurePath

from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import DomainError
from app.models import Document, DocumentBlock, DocumentEvent, DocumentJob, DocumentPage, DocumentVersion
from app.queue import DocumentQueue
from app.repositories.documents import DocumentRepository
from app.schemas.documents import (
    DocumentExtractionResponse, DocumentResponse, DocumentType, DocumentUploadResponse,
    ExtractionBlockResponse, ExtractionPageResponse,
)
from app.security import Principal, utcnow
from app.services.document_processing import enqueue_safely, job_response
from app.storage.base import ObjectStorage, StoredObject
from app.malware import scan


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
    upload_request_key: str | None = None,
    extra_metadata: dict | None = None,
) -> DocumentUploadResponse:
    normalized_mime = validate_file(filename, content_type, content)
    scan(content, settings)
    title = title.strip()
    if not title:
        raise DomainError("title_required", "Document title is required.", 422)
    if kind == DocumentType.TEXTBOOK and not (edition and edition.strip()):
        raise DomainError("textbook_edition_required", "Enter the textbook edition before uploading.", 422)
    repository = DocumentRepository(db)
    _validate_relationships(repository, kind, course_id, subject_id, source_document_id)
    if upload_request_key:
        existing = db.scalar(select(Document).where(Document.upload_request_key == upload_request_key))
        if existing:
            version = repository.latest_version(existing.id); job = repository.latest_job(existing.id)
            if not version or not job:
                raise DomainError("upload_incomplete", "The earlier upload request is incomplete; contact an administrator.", 409)
            return DocumentUploadResponse(document=document_response(existing, version), job=job_response(job))
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
    metadata.update(extra_metadata or {})
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
        upload_request_key=upload_request_key,
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
        stage="deterministic_extraction",
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


def extraction_response(db: Session, document_id: uuid.UUID) -> DocumentExtractionResponse:
    document, version = get_document(db, document_id)
    repository = DocumentRepository(db)
    pages = []
    for page, blocks in repository.pages_with_blocks(version.id):
        pages.append(ExtractionPageResponse(
            id=str(page.id), pageNumber=page.page_number, widthPoints=page.width_points,
            heightPoints=page.height_points, renderAssetId=str(page.render_asset_id),
            originalRenderAssetId=str(page.original_render_asset_id) if page.original_render_asset_id else None,
            printedPageLabel=page.printed_page_label,
            method=page.extraction_method, confidence=page.confidence,
            needsReview=page.needs_review, metadata=page.page_metadata,
            blocks=[ExtractionBlockResponse(
                id=str(block.id), sequenceNumber=block.sequence_number, kind=block.block_kind,
                text=block.text, latex=block.latex, boundingBox=block.bounding_box,
                method=block.extraction_method, confidence=block.confidence,
                needsReview=block.needs_review,
                sourceAssetId=str(block.source_asset_id) if block.source_asset_id else None,
                metadata=block.block_metadata,
            ) for block in blocks],
        ))
    return DocumentExtractionResponse(
        documentId=str(document.id), versionId=str(version.id), status=version.status, pages=pages,
    )


BLOCK_KINDS = {"heading", "paragraph", "table", "question", "subpart", "answer_space", "equation", "image", "diagram"}


def update_extraction_page(db: Session, principal: Principal, document_id: uuid.UUID,
                           page_id: uuid.UUID, printed_page_label: str | None) -> DocumentExtractionResponse:
    document, version = get_document(db, document_id)
    page = db.scalar(select(DocumentPage).where(DocumentPage.id == page_id,
                                                DocumentPage.document_version_id == version.id))
    if not page:
        raise DomainError("document_page_not_found", "The extracted page could not be found.", 404)
    page.printed_page_label = (printed_page_label or "").strip() or None
    page.needs_review = bool(db.scalar(select(DocumentBlock.id).where(
        DocumentBlock.page_id == page.id, DocumentBlock.needs_review.is_(True),
    ).limit(1)))
    page.page_metadata = {**page.page_metadata, "adminReviewed": True, "reviewedBy": str(principal.user.id)}
    db.add(DocumentEvent(document_id=document.id, document_version_id=version.id, actor_id=principal.user.id,
                         event_type="page_reviewed", event_data={"pageNumber": page.page_number,
                                                                  "printedPageLabel": page.printed_page_label}))
    _refresh_topic_document_readiness(db, version.id, principal.user.id)
    db.commit()
    return extraction_response(db, document_id)


def update_extraction_block(db: Session, principal: Principal, document_id: uuid.UUID,
                            block_id: uuid.UUID, *, kind: str, text: str, latex: str | None,
                            sequence_number: int) -> DocumentExtractionResponse:
    document, version = get_document(db, document_id)
    block = db.scalar(select(DocumentBlock).where(DocumentBlock.id == block_id,
                                                   DocumentBlock.document_version_id == version.id))
    if not block:
        raise DomainError("document_block_not_found", "The extracted block could not be found.", 404)
    if kind not in BLOCK_KINDS:
        raise DomainError("invalid_block_kind", "Choose a supported extracted block type.", 422)
    duplicate = db.scalar(select(DocumentBlock).where(
        DocumentBlock.page_id == block.page_id, DocumentBlock.sequence_number == sequence_number,
        DocumentBlock.id != block.id,
    ))
    if duplicate:
        raise DomainError("duplicate_block_order", "Block reading order must be unique on the page.", 409)
    block.block_kind, block.text, block.latex = kind, text.strip(), (latex or "").strip() or None
    block.sequence_number = sequence_number; block.needs_review = False
    block.block_metadata = {**block.block_metadata, "adminReviewed": True, "reviewedBy": str(principal.user.id)}
    page = db.get(DocumentPage, block.page_id)
    if page:
        page.needs_review = bool(db.scalar(select(DocumentBlock.id).where(
            DocumentBlock.page_id == page.id, DocumentBlock.needs_review.is_(True), DocumentBlock.id != block.id,
        )))
    db.add(DocumentEvent(document_id=document.id, document_version_id=version.id, actor_id=principal.user.id,
                         event_type="extraction_block_corrected", event_data={"pageNumber": page.page_number if page else None,
                                                                              "blockId": str(block.id)}))
    _refresh_topic_document_readiness(db, version.id, principal.user.id)
    db.commit()
    return extraction_response(db, document_id)


def _refresh_topic_document_readiness(db: Session, document_version_id: uuid.UUID,
                                      actor_id: uuid.UUID | None = None) -> None:
    from app.models import TextbookTopicDocument
    links = db.scalars(select(TextbookTopicDocument).where(
        TextbookTopicDocument.document_version_id == document_version_id,
    )).all()
    unresolved_pages = db.scalar(select(DocumentPage.id).where(
        DocumentPage.document_version_id == document_version_id, DocumentPage.needs_review.is_(True),
    ).limit(1))
    unresolved_blocks = db.scalar(select(DocumentBlock.id).where(
        DocumentBlock.document_version_id == document_version_id, DocumentBlock.needs_review.is_(True),
    ).limit(1))
    page_exists = db.scalar(select(DocumentPage.id).where(
        DocumentPage.document_version_id == document_version_id,
    ).limit(1))
    complete = bool(page_exists and not unresolved_pages and not unresolved_blocks)
    version = db.get(DocumentVersion, document_version_id)
    document = db.get(Document, version.document_id) if version else None
    was_complete = bool(version and version.status == "completed" and document and document.review_state in {"reviewed", "published"})
    if version and version.status not in {"failed", "removed"}:
        version.status = "completed" if complete else "needs_review"
    if document and document.review_state not in {"published", "rejected"}:
        document.review_state = "reviewed" if complete else "pending"
    for link in links:
        if link.review_status not in {"failed", "superseded", "published"}:
            link.review_status = "ready" if complete else "needs_review"
    if complete and not was_complete and document and actor_id:
        db.add(DocumentEvent(document_id=document.id, document_version_id=document_version_id,
                             actor_id=actor_id, event_type="extraction_review_completed",
                             event_data={"pageCount": len(db.scalars(select(DocumentPage.id).where(
                                 DocumentPage.document_version_id == document_version_id)).all()),
                                         "topicAttachmentCount": len(links)}))


def download_asset(
    db: Session, storage: ObjectStorage, document_id: uuid.UUID, asset_id: uuid.UUID
) -> StoredObject:
    _document, version = get_document(db, document_id)
    asset = DocumentRepository(db).asset(asset_id)
    if not asset or asset.document_version_id != version.id:
        raise DomainError("document_asset_not_found", "Document asset not found.", 404)
    try:
        return storage.get(asset.object_key, asset.mime_type)
    except FileNotFoundError as exc:
        raise DomainError("document_asset_missing", "The extracted asset could not be found.", 500) from exc


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
