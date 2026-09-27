from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import PurePath

from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import DomainError
from app.models import Document, DocumentBlock, DocumentEvent, DocumentJob, DocumentPage, DocumentVersion, TextbookTopicDocument
from app.queue import DocumentQueue
from app.repositories.documents import DocumentRepository
from app.schemas.documents import (
    DocumentExtractionResponse, DocumentResponse, DocumentType, DocumentUploadResponse,
    FinalDocumentBlockResponse, FinalDocumentPageResponse, FinalDocumentResponse,
    ExtractionBlockResponse, ExtractionPageResponse,
)
from app.security import Principal, utcnow
from app.services.document_processing import enqueue_safely, job_response
from app.services.paragraph_reconstruction import RECONSTRUCTION_VERSION, reconstruct_blocks
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
    page.needs_review = not page.printed_page_label or bool(db.scalar(select(DocumentBlock.id).where(
        DocumentBlock.page_id == page.id, DocumentBlock.needs_review.is_(True),
    ).limit(1)))
    page.page_metadata = {**page.page_metadata, "adminReviewed": bool(page.printed_page_label),
                          "printedPageLabelConfirmed": bool(page.printed_page_label),
                          "reviewedBy": str(principal.user.id)}
    db.add(DocumentEvent(document_id=document.id, document_version_id=version.id, actor_id=principal.user.id,
                         event_type="page_reviewed", event_data={"pageNumber": page.page_number,
                                                                  "printedPageLabel": page.printed_page_label}))
    _refresh_topic_document_readiness(db, version.id, principal.user.id)
    db.commit()
    return extraction_response(db, document_id)


def update_extraction_block(db: Session, principal: Principal, document_id: uuid.UUID,
                            block_id: uuid.UUID, *, kind: str, text: str, latex: str | None,
                            sequence_number: int, caption: str | None = None,
                            scientific_content: dict | None = None) -> DocumentExtractionResponse:
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
    metadata = {**block.block_metadata, "adminReviewed": True, "reviewedBy": str(principal.user.id)}
    if scientific_content is not None:
        if scientific_content["text"] != block.text:
            raise DomainError("scientific_text_mismatch",
                              "The formatted scientific text must match the reviewed block text.", 422)
        metadata["scientificContent"] = scientific_content
        metadata["searchAlias"] = scientific_content["plainText"]
        metadata["scientificRendererVersion"] = 1
    else:
        metadata.pop("scientificContent", None)
        metadata.pop("searchAlias", None)
    if caption is not None:
        if kind not in {"image", "diagram", "table"}:
            raise DomainError("caption_requires_visual", "A reviewed caption can only be saved on a visual block.", 422)
        cleaned_caption = " ".join(caption.split())
        if cleaned_caption:
            metadata["reviewedCaption"] = cleaned_caption
        else:
            metadata.pop("reviewedCaption", None)
    block.block_metadata = metadata
    page = db.get(DocumentPage, block.page_id)
    if page:
        page.needs_review = not page.printed_page_label or bool(db.scalar(select(DocumentBlock.id).where(
            DocumentBlock.page_id == page.id, DocumentBlock.needs_review.is_(True), DocumentBlock.id != block.id,
        )))
    db.add(DocumentEvent(document_id=document.id, document_version_id=version.id, actor_id=principal.user.id,
                         event_type="extraction_block_corrected", event_data={"pageNumber": page.page_number if page else None,
                                                                              "blockId": str(block.id)}))
    _refresh_topic_document_readiness(db, version.id, principal.user.id)
    db.commit()
    return extraction_response(db, document_id)


def _block_payload(block: DocumentBlock) -> dict:
    return {"kind": block.block_kind, "text": block.text, "latex": block.latex,
            "bbox": block.bounding_box, "bboxSpace": block.block_metadata.get("bboxSpace", "normalized"),
            "method": block.extraction_method, "confidence": block.confidence,
            "needsReview": block.needs_review, "metadata": block.block_metadata,
            "sourceAssetId": str(block.source_asset_id) if block.source_asset_id else None}


def reconstruction_preview(db: Session, document_id: uuid.UUID) -> dict:
    document, version = get_document(db, document_id)
    links = db.scalars(select(TextbookTopicDocument).where(
        TextbookTopicDocument.document_version_id == version.id)).all()
    if any(link.review_status in {"published", "superseded"} for link in links) or document.review_state == "published":
        raise DomainError("published_document_immutable",
                          "Published textbook evidence cannot be reconstructed. Upload a new source version instead.", 409)
    if links and all(link.role == "visual_reference" for link in links):
        raise DomainError("visual_reference_text_excluded",
                          "Visual Reference OCR is excluded from required text reconstruction.", 409)
    before = 0; after = 0; examples = []; reviewed = 0
    pages = db.scalars(select(DocumentPage).where(
        DocumentPage.document_version_id == version.id).order_by(DocumentPage.page_number)).all()
    for page in pages:
        rows = db.scalars(select(DocumentBlock).where(DocumentBlock.page_id == page.id)
                          .order_by(DocumentBlock.sequence_number)).all()
        rebuilt = reconstruct_blocks([_block_payload(row) for row in rows])
        before += len(rows); after += len(rebuilt)
        reviewed += sum(row.block_metadata.get("adminReviewed") is True for row in rows)
        for old, new in zip(rows, rebuilt):
            if old.text != new["text"] and len(examples) < 10:
                examples.append({"pageNumber": page.page_number, "before": old.text, "after": new["text"]})
    return {"documentId": str(document.id), "version": RECONSTRUCTION_VERSION,
            "pageCount": len(pages), "beforeBlockCount": before, "afterBlockCount": after,
            "reviewedBlockCount": reviewed, "examples": examples}


def reprocess_paragraphs(db: Session, principal: Principal, document_id: uuid.UUID,
                         *, confirm_overwrite_reviewed: bool) -> DocumentExtractionResponse:
    document, version = get_document(db, document_id)
    links = db.scalars(select(TextbookTopicDocument).where(
        TextbookTopicDocument.document_version_id == version.id)).all()
    if any(link.review_status in {"published", "superseded"} for link in links) or document.review_state == "published":
        raise DomainError("published_document_immutable",
                          "Published textbook evidence cannot be reconstructed. Upload a new source version instead.", 409)
    if links and all(link.role == "visual_reference" for link in links):
        raise DomainError("visual_reference_text_excluded",
                          "Visual Reference OCR is excluded from required text reconstruction.", 409)
    pages = db.scalars(select(DocumentPage).where(
        DocumentPage.document_version_id == version.id).order_by(DocumentPage.page_number)).all()
    reviewed = any(block.block_metadata.get("adminReviewed") is True for block in db.scalars(
        select(DocumentBlock).where(DocumentBlock.document_version_id == version.id)).all())
    if reviewed and not confirm_overwrite_reviewed:
        raise DomainError("reviewed_blocks_confirmation_required",
                          "This source contains manual review work. Confirm before reconstructing its draft.", 409)
    before_count = 0; after_count = 0
    for page in pages:
        rows = db.scalars(select(DocumentBlock).where(DocumentBlock.page_id == page.id)
                          .order_by(DocumentBlock.sequence_number)).all()
        before_count += len(rows)
        reconstructed = reconstruct_blocks([_block_payload(row) for row in rows])
        after_count += len(reconstructed)
        sequence_offset = (max((row.sequence_number for row in rows), default=0)
                           + len(rows) + len(reconstructed) + 1)
        for row in rows:
            row.sequence_number += sequence_offset
        db.flush()
        keepers: set[uuid.UUID] = set()
        for sequence, data in enumerate(reconstructed, 1):
            raw_lines = data.get("metadata", {}).get("reconstruction", {}).get("rawLines", [])
            indices = sorted({int(line["sourceIndex"]) for line in raw_lines if line.get("sourceIndex") is not None})
            if not indices:
                source = data.get("metadata", {}).get("sourceLine", {}).get("sourceIndex")
                indices = [int(source)] if source is not None else [sequence - 1]
            keeper = rows[min(indices)]
            keepers.add(keeper.id)
            keeper.sequence_number = sequence
            keeper.text = data["text"]; keeper.bounding_box = data["bbox"]
            keeper.confidence = data["confidence"]; keeper.needs_review = True
            keeper.block_metadata = {**data.get("metadata", {}), "reprocessedBy": str(principal.user.id),
                                     "reconstructionVersion": RECONSTRUCTION_VERSION,
                                     "adminReviewed": False}
        for row in rows:
            if row.id not in keepers:
                db.delete(row)
        db.flush()
        page.needs_review = True
        page.page_metadata = {**page.page_metadata,
                              "paragraphReconstructionVersion": RECONSTRUCTION_VERSION}
    document.review_state = "pending"; version.status = "needs_review"
    for link in links:
        if link.review_status not in {"published", "superseded", "failed"}: link.review_status = "needs_review"
    db.add(DocumentEvent(document_id=document.id, document_version_id=version.id,
        actor_id=principal.user.id, event_type="paragraph_reconstruction_applied",
        event_data={"version": RECONSTRUCTION_VERSION, "beforeBlockCount": before_count,
                    "afterBlockCount": after_count, "overwroteReviewed": bool(reviewed)}))
    db.commit()
    return extraction_response(db, document_id)


def paragraph_operation(db: Session, principal: Principal, document_id: uuid.UUID,
                        block_id: uuid.UUID, *, action: str,
                        split_offset: int | None = None) -> DocumentExtractionResponse:
    document, version = get_document(db, document_id)
    if document.review_state == "published":
        raise DomainError("published_document_immutable", "Published textbook evidence cannot be edited.", 409)
    block = db.scalar(select(DocumentBlock).where(
        DocumentBlock.id == block_id, DocumentBlock.document_version_id == version.id))
    if not block: raise DomainError("document_block_not_found", "The extracted block could not be found.", 404)
    if block.block_kind in {"image", "diagram", "equation", "table"}:
        raise DomainError("paragraph_operation_not_supported", "This structured block cannot be joined or split as a paragraph.", 422)
    event_data = {"blockId": str(block.id), "action": action}
    if action == "join_previous":
        previous = db.scalar(select(DocumentBlock).where(
            DocumentBlock.page_id == block.page_id,
            DocumentBlock.sequence_number < block.sequence_number,
        ).order_by(DocumentBlock.sequence_number.desc()))
        if not previous or previous.block_kind in {"image", "diagram", "equation", "table"}:
            raise DomainError("previous_paragraph_unavailable", "There is no compatible previous paragraph to join.", 409)
        original = f"{previous.block_metadata.get('reconstruction', {}).get('rawText', previous.text)}\n{block.block_metadata.get('reconstruction', {}).get('rawText', block.text)}"
        previous.text = f"{previous.text.rstrip()} {block.text.lstrip()}".strip()
        previous.bounding_box = {"x0": min(previous.bounding_box["x0"], block.bounding_box["x0"]),
            "y0": min(previous.bounding_box["y0"], block.bounding_box["y0"]),
            "x1": max(previous.bounding_box["x1"], block.bounding_box["x1"]),
            "y1": max(previous.bounding_box["y1"], block.bounding_box["y1"])}
        previous.needs_review = True
        clean_metadata = {key: value for key, value in previous.block_metadata.items()
                          if key not in {"scientificContent", "searchAlias"}}
        previous.block_metadata = {**clean_metadata, "adminReviewed": False,
            "reconstruction": {"version": RECONSTRUCTION_VERSION, "rawText": original,
                               "manualOperation": "join_previous"}}
        db.delete(block); db.flush()
    elif action == "split":
        if split_offset is None or split_offset >= len(block.text):
            raise DomainError("invalid_split_offset", "Choose a split point inside the paragraph.", 422)
        left, right = block.text[:split_offset].strip(), block.text[split_offset:].strip()
        if not left or not right: raise DomainError("invalid_split_offset", "Both split paragraphs must contain text.", 422)
        later = db.scalars(select(DocumentBlock).where(
            DocumentBlock.page_id == block.page_id,
            DocumentBlock.sequence_number > block.sequence_number).order_by(DocumentBlock.sequence_number.desc())).all()
        sequence_offset = max(
            [block.sequence_number, *(row.sequence_number for row in later)],
            default=block.sequence_number,
        ) + len(later) + 1
        for row in later: row.sequence_number += sequence_offset
        db.flush()
        for row in later: row.sequence_number = row.sequence_number - sequence_offset + 1
        original = block.block_metadata.get("reconstruction", {}).get("rawText", block.text)
        block.text = left; block.needs_review = True
        clean_metadata = {key: value for key, value in block.block_metadata.items()
                          if key not in {"scientificContent", "searchAlias"}}
        block.block_metadata = {**clean_metadata, "adminReviewed": False,
            "reconstruction": {"version": RECONSTRUCTION_VERSION, "rawText": original,
                               "manualOperation": "split"}}
        db.add(DocumentBlock(document_version_id=version.id, page_id=block.page_id,
            sequence_number=block.sequence_number + 1, block_kind=block.block_kind, text=right,
            latex=None, bounding_box=block.bounding_box, extraction_method=block.extraction_method,
            confidence=block.confidence, needs_review=True, source_asset_id=block.source_asset_id,
            block_metadata={**block.block_metadata, "splitFromBlockId": str(block.id)}))
    elif action == "restore_extracted":
        raw = block.block_metadata.get("reconstruction", {}).get("rawText")
        if not raw: raise DomainError("raw_extraction_unavailable", "No original extracted text is available for this block.", 409)
        block.text = raw; block.needs_review = True
        clean_metadata = {key: value for key, value in block.block_metadata.items()
                          if key not in {"scientificContent", "searchAlias"}}
        block.block_metadata = {**clean_metadata, "adminReviewed": False,
                                "restoredExtraction": True}
    page = db.get(DocumentPage, block.page_id); page.needs_review = True
    event_data["pageNumber"] = page.page_number
    db.add(DocumentEvent(document_id=document.id, document_version_id=version.id,
        actor_id=principal.user.id, event_type="paragraph_review_operation", event_data=event_data))
    _refresh_topic_document_readiness(db, version.id, principal.user.id)
    db.commit(); return extraction_response(db, document_id)


def final_document(db: Session, document_id: uuid.UUID) -> FinalDocumentResponse:
    document, version = get_document(db, document_id); pages_out = []; digest_rows = []; blockers = []
    pages = db.scalars(select(DocumentPage).where(
        DocumentPage.document_version_id == version.id).order_by(DocumentPage.page_number)).all()
    for page in pages:
        if not page.printed_page_label: blockers.append(f"Page {page.page_number} needs a Printed page label.")
        blocks_out = []
        blocks = db.scalars(select(DocumentBlock).where(DocumentBlock.page_id == page.id)
                            .order_by(DocumentBlock.sequence_number)).all()
        for block in blocks:
            if block.needs_review: blockers.append(f"Page {page.page_number}, block {block.sequence_number} needs review.")
            raw = block.block_metadata.get("reconstruction", {}).get("rawText", block.text)
            digest_rows.append(f"{page.page_number}:{page.printed_page_label}:{block.sequence_number}:{block.block_kind}:{block.text}:{block.latex or ''}:{json.dumps(block.block_metadata.get('scientificContent'), sort_keys=True)}")
            blocks_out.append(FinalDocumentBlockResponse(id=str(block.id), pageId=str(page.id),
                pageNumber=page.page_number, printedPageLabel=page.printed_page_label,
                sequenceNumber=block.sequence_number, kind=block.block_kind, text=block.text,
                latex=block.latex, confidence=block.confidence, needsReview=block.needs_review,
                rawText=raw, sourceAssetId=str(block.source_asset_id) if block.source_asset_id else None,
                metadata=block.block_metadata))
        pages_out.append(FinalDocumentPageResponse(id=str(page.id), pageNumber=page.page_number,
            printedPageLabel=page.printed_page_label, renderAssetId=str(page.original_render_asset_id or page.render_asset_id),
            blocks=blocks_out))
    content_hash = hashlib.sha256("\n".join(digest_rows).encode()).hexdigest()
    confirmation = document.source_metadata.get("finalDocumentReview", {})
    return FinalDocumentResponse(documentId=str(document.id), versionId=str(version.id),
        reconstructionVersion=RECONSTRUCTION_VERSION, contentHash=content_hash,
        confirmed=confirmation.get("contentHash") == content_hash,
        confirmedAt=confirmation.get("confirmedAt"), blockers=blockers, pages=pages_out)


def confirm_final_document(db: Session, principal: Principal, document_id: uuid.UUID,
                           *, confirm_complete: bool) -> FinalDocumentResponse:
    if not confirm_complete: raise DomainError("final_document_confirmation_required", "Confirm the complete reviewed document.", 422)
    document, version = get_document(db, document_id); result = final_document(db, document_id)
    if result.blockers:
        raise DomainError("final_document_not_ready", "Resolve every document review item before confirmation.", 409,
                          [{"message": value} for value in result.blockers])
    confirmed_at = utcnow().isoformat()
    document.source_metadata = {**document.source_metadata, "finalDocumentReview": {
        "contentHash": result.contentHash, "confirmedAt": confirmed_at,
        "confirmedBy": str(principal.user.id), "reconstructionVersion": RECONSTRUCTION_VERSION,
        "rendererVersion": 1}}
    db.add(DocumentEvent(document_id=document.id, document_version_id=version.id,
        actor_id=principal.user.id, event_type="final_reviewed_document_confirmed",
        event_data={"contentHash": result.contentHash, "reconstructionVersion": RECONSTRUCTION_VERSION}))
    db.commit(); return final_document(db, document_id)


def _refresh_topic_document_readiness(db: Session, document_version_id: uuid.UUID,
                                      actor_id: uuid.UUID | None = None) -> None:
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
    missing_label = db.scalar(select(DocumentPage.id).where(
        DocumentPage.document_version_id == document_version_id,
        (DocumentPage.printed_page_label.is_(None)) | (DocumentPage.printed_page_label == ""),
    ).limit(1))
    text_complete = bool(page_exists and not missing_label and not unresolved_pages and not unresolved_blocks)
    visual_complete = bool(page_exists and not missing_label)
    complete = visual_complete if links and all(link.role == "visual_reference" for link in links) else text_complete
    version = db.get(DocumentVersion, document_version_id)
    document = db.get(Document, version.document_id) if version else None
    was_complete = bool(version and version.status == "completed" and document and document.review_state in {"reviewed", "published"})
    if version and version.status not in {"failed", "removed"} and not (
        document and document.review_state in {"published", "rejected"}
    ):
        version.status = "completed" if complete else "needs_review"
    if document and document.review_state not in {"published", "rejected"} and not (
        version and version.status in {"failed", "removed"}
    ):
        document.review_state = "reviewed" if complete else "pending"
    for link in links:
        if link.review_status not in {"failed", "superseded", "published"}:
            link_complete = visual_complete if link.role == "visual_reference" else text_complete
            link.review_status = "ready" if link_complete else "needs_review"
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
