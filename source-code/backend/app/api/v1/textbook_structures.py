from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.textbook_structures import (
    GroupSaveRequest, PublishStructureRequest, PublishTopicContentRequest, ReorderRequest, TextbookCreateRequest,
    TextbookListResponse, TextbookResponse, TextbookUpdateRequest, TopicDocumentRoleUpdateRequest,
    TopicDocumentMoveRequest,
    TopicDocumentSourceResponse, TopicLaunchReadinessResponse, TopicQualityReport, TopicRetrievalPreflightRequest,
    TopicRetrievalPreflightResponse, TopicSaveRequest, TopicReviewChecklistResponse,
    TopicVisualAssetResponse, TopicVisualAssetUpdateRequest,
)
from app.security import Principal
from app.services import textbook_structures
from app.queue import DocumentQueue, get_document_queue
from app.storage import ObjectStorage, get_storage
from app.schemas.documents import DocumentUploadResponse, TopicPartBatchRequest, TopicPartSuggestion, TopicPartSuggestionRequest


router = APIRouter(prefix="/admin/textbooks", tags=["textbook structures"])


@router.get("", response_model=TextbookListResponse)
def list_textbooks(_principal: Annotated[Principal, Depends(require_roles("admin"))],
                   db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.list_textbooks(db)


@router.post("", response_model=TextbookResponse, status_code=status.HTTP_201_CREATED)
def create_textbook(payload: TextbookCreateRequest,
                    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                    db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.create_textbook(db, principal, payload)


@router.get("/{textbook_ref}", response_model=TextbookResponse)
def get_textbook(textbook_ref: str, _principal: Annotated[Principal, Depends(require_roles("admin"))],
                 db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.get_textbook(db, textbook_ref)


@router.get("/{textbook_ref}/topics/{topic_ref}/quality", response_model=TopicQualityReport)
def topic_quality(textbook_ref: str, topic_ref: str,
                  _principal: Annotated[Principal, Depends(require_roles("admin"))],
                  db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.get_topic_quality(db, textbook_ref, topic_ref)


@router.get("/{textbook_ref}/topics/{topic_ref}/sources", response_model=list[TopicDocumentSourceResponse])
def topic_sources(textbook_ref: str, topic_ref: str,
                  _principal: Annotated[Principal, Depends(require_roles("admin"))],
                  db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.list_topic_sources(db, textbook_ref, topic_ref)


@router.get("/{textbook_ref}/topics/{topic_ref}/review-checklist",
            response_model=TopicReviewChecklistResponse)
def review_checklist(textbook_ref: str, topic_ref: str,
                     _principal: Annotated[Principal, Depends(require_roles("admin"))],
                     db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.topic_review_checklist(db, textbook_ref, topic_ref)


@router.post("/{textbook_ref}/topics/{topic_ref}/sources/apply-recommended-roles",
             response_model=list[TopicDocumentSourceResponse])
def apply_recommended_roles(textbook_ref: str, topic_ref: str,
                            principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                            db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.apply_recommended_topic_source_roles(
        db, principal, textbook_ref, topic_ref)


@router.get("/{textbook_ref}/topics/{topic_ref}/launch-readiness",
            response_model=TopicLaunchReadinessResponse)
def topic_launch_readiness(textbook_ref: str, topic_ref: str,
                           _principal: Annotated[Principal, Depends(require_roles("admin"))],
                           db: Annotated[Session, Depends(get_db)],
                           student_id: Annotated[str | None, Query(alias="studentId")] = None):
    return textbook_structures.topic_launch_readiness(db, textbook_ref, topic_ref, student_id)


@router.post("/{textbook_ref}/topics/{topic_ref}/retrieval-preflight",
             response_model=TopicRetrievalPreflightResponse)
def run_topic_retrieval_preflight(textbook_ref: str, topic_ref: str,
                                  payload: TopicRetrievalPreflightRequest,
                                  principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                                  db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.run_retrieval_preflight(db, principal, textbook_ref, topic_ref, payload.queries)


@router.patch("/{textbook_ref}/topics/{topic_ref}/sources/{document_id}",
              response_model=list[TopicDocumentSourceResponse])
def update_topic_source(textbook_ref: str, topic_ref: str, document_id: str,
                        payload: TopicDocumentRoleUpdateRequest,
                        principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                        db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.update_topic_source_role(
        db, principal, textbook_ref, topic_ref, document_id, payload.role,
    )


@router.delete("/{textbook_ref}/topics/{topic_ref}/sources/{document_id}",
               response_model=list[TopicDocumentSourceResponse])
def detach_topic_source(textbook_ref: str, topic_ref: str, document_id: str,
                        principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                        db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.detach_topic_source(db, principal, textbook_ref, topic_ref, document_id)


@router.post("/{textbook_ref}/topics/{topic_ref}/sources/{document_id}/move",
             response_model=list[TopicDocumentSourceResponse])
def move_topic_source(textbook_ref: str, topic_ref: str, document_id: str,
                      payload: TopicDocumentMoveRequest,
                      principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                      db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.move_topic_source(
        db, principal, textbook_ref, topic_ref, document_id, payload.targetTopicRef)


@router.get("/{textbook_ref}/topics/{topic_ref}/sources/{document_id}/visual-assets",
            response_model=list[TopicVisualAssetResponse])
def topic_visual_assets(textbook_ref: str, topic_ref: str, document_id: str,
                        _principal: Annotated[Principal, Depends(require_roles("admin"))],
                        db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.list_topic_visual_assets(db, textbook_ref, topic_ref, document_id)


@router.patch("/{textbook_ref}/topics/{topic_ref}/sources/{document_id}/visual-assets/{asset_ref}",
              response_model=list[TopicVisualAssetResponse])
def review_topic_visual_asset(textbook_ref: str, topic_ref: str, document_id: str,
                              asset_ref: str, payload: TopicVisualAssetUpdateRequest,
                              principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                              db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.update_topic_visual_asset(
        db, principal, textbook_ref, topic_ref, document_id, asset_ref,
        payload.status, payload.caption, payload.altText)


@router.post("/{textbook_ref}", response_model=TextbookResponse)
def update_textbook(textbook_ref: str, payload: TextbookUpdateRequest,
                    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                    db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.update_textbook(db, principal, textbook_ref, payload)


@router.delete("/{textbook_ref}", response_model=TextbookResponse)
def archive_textbook(textbook_ref: str,
                     principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                     db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.archive_textbook(db, principal, textbook_ref)


@router.post("/{textbook_ref}/groups", response_model=TextbookResponse)
def create_group(textbook_ref: str, payload: GroupSaveRequest,
                 principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                 db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.save_group(db, principal, textbook_ref, payload)


@router.post("/{textbook_ref}/groups/reorder", response_model=TextbookResponse)
def reorder_groups(textbook_ref: str, payload: ReorderRequest,
                   principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                   db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.reorder_groups(db, principal, textbook_ref, payload)


@router.post("/{textbook_ref}/groups/{group_ref}", response_model=TextbookResponse)
def update_group(textbook_ref: str, group_ref: str, payload: GroupSaveRequest,
                 principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                 db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.save_group(db, principal, textbook_ref, payload, group_ref)


@router.delete("/{textbook_ref}/groups/{group_ref}", response_model=TextbookResponse)
def remove_group(textbook_ref: str, group_ref: str,
                 principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                 db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.remove_group(db, principal, textbook_ref, group_ref)


@router.post("/{textbook_ref}/groups/{group_ref}/topics", response_model=TextbookResponse)
def create_topic(textbook_ref: str, group_ref: str, payload: TopicSaveRequest,
                 principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                 db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.save_topic(db, principal, textbook_ref, group_ref, payload)


@router.post("/{textbook_ref}/groups/{group_ref}/topics/reorder", response_model=TextbookResponse)
def reorder_topics(textbook_ref: str, group_ref: str, payload: ReorderRequest,
                   principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                   db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.reorder_topics(db, principal, textbook_ref, group_ref, payload)


@router.post("/{textbook_ref}/groups/{group_ref}/topics/{topic_ref}", response_model=TextbookResponse)
def update_topic(textbook_ref: str, group_ref: str, topic_ref: str, payload: TopicSaveRequest,
                 principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                 db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.save_topic(db, principal, textbook_ref, group_ref, payload, topic_ref)


@router.delete("/{textbook_ref}/topics/{topic_ref}", response_model=TextbookResponse)
def remove_topic(textbook_ref: str, topic_ref: str,
                 principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                 db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.remove_topic(db, principal, textbook_ref, topic_ref)


@router.post("/{textbook_ref}/publish", response_model=TextbookResponse)
def publish_structure(textbook_ref: str, payload: PublishStructureRequest,
                      principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                      db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.publish_structure(db, principal, textbook_ref, payload)


@router.post("/{textbook_ref}/topics/{topic_ref}/publish", response_model=TextbookResponse)
def publish_topic_content(textbook_ref: str, topic_ref: str, payload: PublishTopicContentRequest,
                          principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                          db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.publish_topic_content(db, principal, textbook_ref, topic_ref, payload)


@router.post("/{textbook_ref}/topics/suggest", response_model=list[TopicPartSuggestion])
def suggest_topic_parts(textbook_ref: str, payload: TopicPartSuggestionRequest,
                        _principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                        db: Annotated[Session, Depends(get_db)]):
    return textbook_structures.suggest_topics(db, textbook_ref, payload.filenames)


@router.post("/{textbook_ref}/topics/{topic_ref}/documents", response_model=DocumentUploadResponse,
             status_code=status.HTTP_201_CREATED)
def upload_topic_part(textbook_ref: str, topic_ref: str,
                      content: Annotated[bytes, Body(media_type="application/octet-stream")],
                      principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                      db: Annotated[Session, Depends(get_db)],
                      storage: Annotated[ObjectStorage, Depends(get_storage)],
                      queue: Annotated[DocumentQueue, Depends(get_document_queue)],
                      filename: Annotated[str, Header(alias="X-Filename", min_length=1, max_length=255)],
                      content_type: Annotated[str, Header(alias="Content-Type")],
                      idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=100)],
                      role: Annotated[str, Query(max_length=24)] = "primary",
                      printed_start_page: Annotated[str | None, Query(alias="printedStartPage", max_length=24)] = None,
                      printed_end_page: Annotated[str | None, Query(alias="printedEndPage", max_length=24)] = None):
    return textbook_structures.upload_topic_part(
        db, storage, queue, principal, textbook_ref, topic_ref, content=content, filename=filename,
        content_type=content_type, role=role, printed_start_page=printed_start_page,
        printed_end_page=printed_end_page, idempotency_key=idempotency_key,
    )


@router.post("/{textbook_ref}/topics/{topic_ref}/documents/batch", response_model=list[DocumentUploadResponse],
             status_code=status.HTTP_201_CREATED)
def upload_topic_parts_batch(textbook_ref: str, topic_ref: str, payload: TopicPartBatchRequest,
                             principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                             db: Annotated[Session, Depends(get_db)],
                             storage: Annotated[ObjectStorage, Depends(get_storage)],
                             queue: Annotated[DocumentQueue, Depends(get_document_queue)]):
    return textbook_structures.upload_topic_parts_batch(db, storage, queue, principal,
                                                        textbook_ref, topic_ref, payload)
