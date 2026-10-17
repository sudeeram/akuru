import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.official_paper_reviews import (
    CreateReviewCrop, PaperReviewResponse, ReviewCropResponse, SaveReviewQuestion, SeedPaperReview, StartPaperReview,
)
from app.security import Principal
from app.services import official_paper_reviews
from app.storage import ObjectStorage, get_storage


router = APIRouter(prefix="/admin/official-paper-reviews", tags=["official-paper-reviews"])


@router.get("/{paper_id}", response_model=PaperReviewResponse)
def get_review(paper_id: uuid.UUID,
               _principal: Annotated[Principal, Depends(require_roles("admin"))],
               db: Annotated[Session, Depends(get_db)]):
    return official_paper_reviews.get(db, paper_id)


@router.get("/{paper_id}/topics")
def published_topics(paper_id: uuid.UUID,
                     _principal: Annotated[Principal, Depends(require_roles("admin"))],
                     db: Annotated[Session, Depends(get_db)]):
    return official_paper_reviews.published_topics(db, paper_id)


@router.get("/{paper_id}/topics/{topic_ref}/evidence")
def topic_evidence(paper_id: uuid.UUID, topic_ref: str,
                   _principal: Annotated[Principal, Depends(require_roles("admin"))],
                   db: Annotated[Session, Depends(get_db)]):
    return official_paper_reviews.published_topic_evidence(db, paper_id, topic_ref)


@router.post("/{paper_id}/start", response_model=PaperReviewResponse)
def start_review(paper_id: uuid.UUID, payload: StartPaperReview,
                 principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                 db: Annotated[Session, Depends(get_db)]):
    return official_paper_reviews.start(db, principal, paper_id, payload)


@router.post("/{paper_id}/questions", response_model=PaperReviewResponse)
def save_question(paper_id: uuid.UUID, payload: SaveReviewQuestion,
                  principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                  db: Annotated[Session, Depends(get_db)]):
    return official_paper_reviews.save_question(db, principal, paper_id, payload)


@router.post("/{paper_id}/visual-crops", response_model=ReviewCropResponse)
def create_visual_crop(paper_id: uuid.UUID, payload: CreateReviewCrop,
                       principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                       db: Annotated[Session, Depends(get_db)],
                       storage: Annotated[ObjectStorage, Depends(get_storage)]):
    return official_paper_reviews.create_review_crop(db, storage, principal, paper_id, payload)


@router.get("/{paper_id}/visual-crops", response_model=list[ReviewCropResponse])
def list_visual_crops(paper_id: uuid.UUID,
                      _principal: Annotated[Principal, Depends(require_roles("admin"))],
                      db: Annotated[Session, Depends(get_db)]):
    return official_paper_reviews.review_crops(db, paper_id)


@router.post("/{paper_id}/visual-candidates/generate")
def generate_visual_candidates(paper_id: uuid.UUID,
                               principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                               db: Annotated[Session, Depends(get_db)],
                               storage: Annotated[ObjectStorage, Depends(get_storage)]):
    return official_paper_reviews.generate_review_candidates(db, storage, principal, paper_id)


@router.post("/{paper_id}/seed", response_model=PaperReviewResponse)
def seed_review(paper_id: uuid.UUID, payload: SeedPaperReview,
                principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                db: Annotated[Session, Depends(get_db)]):
    return official_paper_reviews.seed(db, principal, paper_id, payload)


@router.post("/{paper_id}/prepare-official-drafts")
def prepare_official_drafts(paper_id: uuid.UUID,
                            principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
                            db: Annotated[Session, Depends(get_db)]):
    return official_paper_reviews.prepare_official_drafts(db, principal, paper_id)
