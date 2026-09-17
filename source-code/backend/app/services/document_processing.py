from __future__ import annotations

import multiprocessing
import hashlib
import re
import resource
import sys
import uuid
from datetime import timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.errors import DomainError
from app.config import get_settings
from app.models import (
    DocumentAsset, DocumentBlock, DocumentJob, DocumentPage, DocumentStageRun, DocumentVersion,
    TextbookTopicDocument,
)
from app.queue import DocumentQueue, QueueUnavailable
from app.repositories.documents import DocumentRepository
from app.schemas.documents import DocumentJobResponse
from app.security import utcnow
from app.services.document_extraction import extract_document
from app.services.document_processing_types import ProcessingFailure
from app.storage import ObjectStorage, get_storage


def job_response(job: DocumentJob) -> DocumentJobResponse:
    return DocumentJobResponse(
        id=str(job.id),
        documentId=str(job.document_id),
        documentVersionId=str(job.document_version_id),
        stage=job.stage,
        status=job.status,
        progress=job.progress,
        attemptCount=job.attempt_count,
        extractionVersion=job.extraction_version,
        errorCode=job.error_code,
        errorMessage=job.error_message,
        result=job.result_data,
        queuedAt=job.queued_at,
        startedAt=job.started_at,
        completedAt=job.completed_at,
    )


def get_job(db: Session, document_id: uuid.UUID, job_id: uuid.UUID | None = None) -> DocumentJob:
    repository = DocumentRepository(db)
    job = repository.job(job_id) if job_id else repository.latest_job(document_id)
    if not job or job.document_id != document_id:
        raise DomainError("document_job_not_found", "Document processing job not found.", 404)
    return job


def enqueue_safely(
    db: Session,
    queue: DocumentQueue,
    job: DocumentJob,
    repository: DocumentRepository,
    actor_id: uuid.UUID,
) -> None:
    try:
        queue.enqueue(job.id)
    except QueueUnavailable:
        repository.add_event(
            repository.document(job.document_id),
            repository.version(job.document_version_id),
            actor_id,
            "queue_publish_deferred",
            {"jobId": str(job.id)},
        )
        db.commit()


def retry_job(db: Session, queue: DocumentQueue, document_id: uuid.UUID, actor_id: uuid.UUID) -> DocumentJob:
    repository = DocumentRepository(db)
    job = get_job(db, document_id)
    if job.status != "failed":
        raise DomainError("document_not_failed", "Only a failed document can be retried.", 409)
    version = repository.version(job.document_version_id)
    settings = get_settings()
    job.status = "queued"
    job.progress = 0
    job.error_code = None
    job.error_message = None
    job.queued_at = utcnow()
    job.started_at = None
    job.heartbeat_at = None
    job.completed_at = None
    # A retry must use the currently reviewed processing ceilings. Otherwise a
    # job that exhausted an older limit can never benefit from an operator's
    # configuration correction.
    job.max_seconds = settings.document_job_timeout_seconds
    job.max_memory_mb = settings.document_job_memory_mb
    job.max_pages = settings.document_max_pages
    version.status = "queued"
    repository.add_event(
        repository.document(document_id), version, actor_id, "retry_queued", {"jobId": str(job.id)}
    )
    db.commit()
    enqueue_safely(db, queue, job, repository, actor_id)
    return job


def preflight(content: bytes, mime_type: str, max_pages: int) -> dict:
    if mime_type == "application/pdf":
        page_count = len(re.findall(rb"/Type\s*/Page\b", content))
        if page_count == 0:
            raise ProcessingFailure("page_count_unknown", "The PDF page count could not be determined.")
    else:
        page_count = 1
    if page_count > max_pages:
        raise ProcessingFailure(
            "page_limit_exceeded",
            f"The document contains {page_count} pages; the processing limit is {max_pages}.",
        )
    return {"pageCount": page_count, "contentType": mime_type}


def _isolated_extraction(
    connection,
    content: bytes,
    mime_type: str,
    subject_id: str,
    max_pages: int,
    max_memory_mb: int,
    render_dpi: int,
    ocr_min_characters: int,
    tesseract_command: str,
) -> None:
    try:
        if sys.platform.startswith("linux"):
            memory_bytes = max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        connection.send(("ok", extract_document(
            content, mime_type, subject_id, max_pages, render_dpi,
            ocr_min_characters, tesseract_command,
        )))
    except ProcessingFailure as exc:
        connection.send(("failure", (exc.code, exc.message)))
    except MemoryError:
        connection.send(("failure", (
            "processing_resource_limit",
            "Document processing exceeded its configured memory limit. An administrator can increase the limit and retry.",
        )))
    except BaseException:
        connection.send(("failure", ("processing_failed", "Document preflight failed safely.")))
    finally:
        connection.close()


def run_isolated_extraction(
    content: bytes,
    mime_type: str,
    subject_id: str,
    max_pages: int,
    max_memory_mb: int,
    timeout_seconds: int,
    render_dpi: int,
    ocr_min_characters: int,
    tesseract_command: str,
) -> dict:
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=False)
    process = context.Process(
        target=_isolated_extraction,
        args=(
            child, content, mime_type, subject_id, max_pages, max_memory_mb,
            render_dpi, ocr_min_characters, tesseract_command,
        ),
        daemon=True,
    )
    process.start()
    child.close()
    if not parent.poll(timeout_seconds):
        process.terminate()
        process.join(5)
        raise ProcessingFailure("processing_timeout", "Document processing exceeded its time limit.")
    try:
        outcome, payload = parent.recv()
    except EOFError as exc:
        process.join(5)
        raise ProcessingFailure(
            "processing_resource_limit", "Document processing stopped at its configured resource limit."
        ) from exc
    process.join(5)
    if outcome == "failure":
        raise ProcessingFailure(*payload)
    return payload


def _store_asset(
    db: Session,
    storage: ObjectStorage,
    version: DocumentVersion,
    extraction_version: str,
    page_number: int,
    sequence: int,
    kind: str,
    mime_type: str,
    content: bytes,
    bounding_box: dict | None,
    metadata: dict | None = None,
) -> DocumentAsset:
    digest = hashlib.sha256(content).hexdigest()
    extension = {"image/png": "png", "image/jpeg": "jpg"}.get(mime_type, "bin")
    key = (
        f"derived/{version.id}/{extraction_version}/page-{page_number:04d}/"
        f"{sequence:04d}-{kind}-{digest[:16]}.{extension}"
    )
    storage.put(key, content, mime_type)
    asset = DocumentAsset(
        document_version_id=version.id, asset_kind=kind, object_key=key,
        mime_type=mime_type, sha256=digest, size_bytes=len(content),
        page_number=page_number, bounding_box=bounding_box,
        asset_metadata=metadata or {},
    )
    db.add(asset)
    db.flush()
    return asset


def persist_extraction(
    db: Session,
    storage: ObjectStorage,
    version: DocumentVersion,
    extraction_version: str,
    extraction: dict,
) -> dict:
    page_ids = select(DocumentPage.id).where(DocumentPage.document_version_id == version.id)
    db.execute(delete(DocumentBlock).where(DocumentBlock.page_id.in_(page_ids)))
    db.execute(delete(DocumentPage).where(DocumentPage.document_version_id == version.id))
    db.execute(delete(DocumentAsset).where(DocumentAsset.document_version_id == version.id))
    db.flush()
    for page_data in extraction["pages"]:
        page_number = page_data["pageNumber"]
        original_asset = _store_asset(
            db, storage, version, extraction_version, page_number, 0, "page_original",
            "image/png", page_data.get("originalRender", page_data["render"]), None,
            {"dpi": extraction["renderDpi"], "preservedOriginal": True},
        )
        render_asset = _store_asset(
            db, storage, version, extraction_version, page_number, 1, "page_render",
            "image/png", page_data["render"], None, {"dpi": extraction["renderDpi"]},
        )
        asset_rows = []
        for index, asset_data in enumerate(page_data["assets"], 1):
            asset_rows.append(_store_asset(
                db, storage, version, extraction_version, page_number, index,
                asset_data["kind"], asset_data["mimeType"], asset_data["content"],
                asset_data.get("bbox"), {"bboxSpace": asset_data.get("bboxSpace", "pdf_points")},
            ))
        page = DocumentPage(
            document_version_id=version.id, page_number=page_number,
            printed_page_label=page_data.get("printedPageLabel"),
            width_points=page_data["widthPoints"], height_points=page_data["heightPoints"],
            render_asset_id=render_asset.id, original_render_asset_id=original_asset.id,
            native_text=page_data["nativeText"],
            extraction_method=page_data["method"], confidence=page_data["confidence"],
            needs_review=page_data["needsReview"], page_metadata=page_data["metadata"],
        )
        db.add(page)
        db.flush()
        for sequence, block_data in enumerate(page_data["blocks"], 1):
            source_index = block_data.get("sourceAssetIndex")
            db.add(DocumentBlock(
                document_version_id=version.id, page_id=page.id, sequence_number=sequence,
                block_kind=block_data["kind"], text=block_data["text"], latex=block_data["latex"],
                bounding_box=block_data["bbox"], extraction_method=block_data["method"],
                confidence=block_data["confidence"], needs_review=block_data["needsReview"],
                source_asset_id=asset_rows[source_index].id if source_index is not None else None,
                block_metadata={"bboxSpace": block_data["bboxSpace"], **block_data.get("metadata", {})},
            ))
    db.flush()
    return {key: value for key, value in extraction.items() if key != "pages"}


def process_job(job_id: uuid.UUID, storage: ObjectStorage | None = None) -> str:
    storage = storage or get_storage()
    settings = get_settings()
    with SessionLocal() as db:
        repository = DocumentRepository(db)
        job = repository.job(job_id, lock=True)
        if not job or job.status != "queued":
            db.rollback()
            return "skipped"
        document = repository.document(job.document_id)
        version = repository.version(job.document_version_id)
        if not document or document.removed_at or not version:
            job.status = "failed"
            job.error_code = "document_unavailable"
            job.error_message = "The document is no longer available for processing."
            job.completed_at = utcnow()
            db.commit()
            return "failed"
        stage_run = repository.stage_run(version.id, job.stage, job.extraction_version)
        if stage_run and stage_run.status == "completed" and stage_run.input_checksum == version.sha256:
            job.status = "needs_review"
            job.progress = 100
            job.result_data = stage_run.output_data
            job.completed_at = utcnow()
            version.status = "needs_review"
            db.commit()
            return "idempotent"
        now = utcnow()
        if stage_run is None:
            stage_run = DocumentStageRun(
                document_version_id=version.id,
                stage=job.stage,
                extraction_version=job.extraction_version,
                status="processing",
                input_checksum=version.sha256,
            )
            db.add(stage_run)
        else:
            stage_run.status = "processing"
            stage_run.output_data = {}
            stage_run.completed_at = None
        job.status = "processing"
        job.progress = 10
        job.attempt_count += 1
        job.started_at = now
        job.heartbeat_at = now
        job.error_code = None
        job.error_message = None
        version.status = "processing"
        repository.add_event(document, version, document.uploaded_by, "processing_started", {"jobId": str(job.id)})
        db.commit()

        try:
            stored = storage.get(version.object_key, version.mime_type)
            extraction = run_isolated_extraction(
                stored.content, version.mime_type, document.subject_id, job.max_pages,
                job.max_memory_mb, job.max_seconds, settings.document_render_dpi,
                settings.document_ocr_min_characters, settings.tesseract_command,
            )
            result = persist_extraction(db, storage, version, job.extraction_version, extraction)
        except (ProcessingFailure, FileNotFoundError) as exc:
            failure = exc if isinstance(exc, ProcessingFailure) else ProcessingFailure(
                "document_bytes_missing", "The original document bytes could not be found."
            )
            job.status = "failed"
            job.progress = 100
            job.error_code = failure.code
            job.error_message = failure.message
            job.completed_at = utcnow()
            version.status = "failed"
            link = db.scalar(select(TextbookTopicDocument).where(TextbookTopicDocument.document_version_id == version.id))
            if link: link.review_status = "failed"
            stage_run.status = "failed"
            stage_run.completed_at = job.completed_at
            repository.add_event(
                document, version, document.uploaded_by, "processing_failed",
                {"jobId": str(job.id), "code": failure.code},
            )
            db.commit()
            return "failed"

        job.status = "needs_review"
        job.progress = 100
        job.result_data = result
        job.completed_at = utcnow()
        version.status = "needs_review"
        link = db.scalar(select(TextbookTopicDocument).where(TextbookTopicDocument.document_version_id == version.id))
        if link: link.review_status = "needs_review" if result.get("reviewFlagCount", 0) else "ready"
        stage_run.status = "completed"
        stage_run.output_data = result
        stage_run.completed_at = job.completed_at
        repository.add_event(
            document, version, document.uploaded_by, "extraction_completed",
            {"jobId": str(job.id), **result},
        )
        db.commit()
        return "needs_review"


def recover_queued_jobs(queue: DocumentQueue, stale_after_seconds: int = 300) -> int:
    with SessionLocal() as db:
        cutoff = utcnow() - timedelta(seconds=stale_after_seconds)
        stale_ids = list(db.execute(select(DocumentJob.id).where(
            DocumentJob.status == "processing",
            DocumentJob.heartbeat_at < cutoff,
        )).scalars())
        if stale_ids:
            db.execute(update(DocumentJob).where(DocumentJob.id.in_(stale_ids)).values(
                status="queued", progress=0, error_code=None,
                error_message=None, started_at=None, completed_at=None,
            ))
            db.execute(update(DocumentVersion).where(
                DocumentVersion.id.in_(select(DocumentJob.document_version_id).where(DocumentJob.id.in_(stale_ids)))
            ).values(status="queued"))
            db.commit()
        job_ids = DocumentRepository(db).queued_job_ids()
        for job_id in job_ids:
            queue.enqueue(job_id)
        return len(job_ids)
