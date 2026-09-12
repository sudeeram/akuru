import uuid
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Body, Depends, Header, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.documents import DocumentListResponse, DocumentResponse, DocumentType
from app.security import Principal
from app.services import documents
from app.storage import ObjectStorage, get_storage


router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentListResponse)
def list_documents(
    _principal: Annotated[Principal, Depends(require_roles("admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentListResponse:
    return DocumentListResponse(documents=documents.list_documents(db))


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    content: Annotated[bytes, Body(media_type="application/octet-stream")],
    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[ObjectStorage, Depends(get_storage)],
    filename: Annotated[str, Header(alias="X-Filename", min_length=1, max_length=255)],
    content_type: Annotated[str, Header(alias="Content-Type")],
    kind: Annotated[DocumentType, Query()],
    course_id: Annotated[str, Query(alias="courseId", min_length=1, max_length=32)],
    subject_id: Annotated[str, Query(alias="subjectId", min_length=1, max_length=32)],
    title: Annotated[str, Query(min_length=1, max_length=240)],
    edition: Annotated[str | None, Query(max_length=80)] = None,
    year: Annotated[int | None, Query(ge=1900, le=2100)] = None,
    session: Annotated[str | None, Query(max_length=80)] = None,
    component: Annotated[str | None, Query(max_length=80)] = None,
    variant: Annotated[str | None, Query(max_length=80)] = None,
    source_document_id: Annotated[uuid.UUID | None, Query(alias="sourceDocumentId")] = None,
    publisher: Annotated[str | None, Query(max_length=160)] = None,
    isbn: Annotated[str | None, Query(max_length=40)] = None,
    source_url: Annotated[str | None, Query(alias="sourceUrl", max_length=500)] = None,
) -> DocumentResponse:
    return documents.upload_document(
        db,
        storage,
        principal,
        content=content,
        filename=filename,
        content_type=content_type,
        kind=kind,
        course_id=course_id,
        subject_id=subject_id,
        title=title,
        edition=edition,
        publication_year=year,
        exam_session=session,
        component=component,
        variant=variant,
        source_document_id=source_document_id,
        publisher=publisher,
        isbn=isbn,
        source_url=source_url,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def document_status(
    document_id: uuid.UUID,
    _principal: Annotated[Principal, Depends(require_roles("admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentResponse:
    document, version = documents.get_document(db, document_id)
    return documents.document_response(document, version)


@router.get("/{document_id}/content")
def download_document(
    document_id: uuid.UUID,
    _principal: Annotated[Principal, Depends(require_roles("admin"))],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[ObjectStorage, Depends(get_storage)],
) -> Response:
    document, version = documents.get_document(db, document_id)
    stored = documents.download_document(db, storage, document_id)
    disposition = f"attachment; filename*=UTF-8''{quote(version.original_filename)}"
    return Response(
        content=stored.content,
        media_type=stored.content_type,
        headers={
            "Content-Disposition": disposition,
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/{document_id}/retry", response_model=DocumentResponse)
def retry_document(
    document_id: uuid.UUID,
    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> DocumentResponse:
    return documents.retry_document(db, principal, document_id)


@router.delete("/{document_id}", status_code=204)
def remove_document(
    document_id: uuid.UUID,
    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    documents.remove_document(db, principal, document_id)
