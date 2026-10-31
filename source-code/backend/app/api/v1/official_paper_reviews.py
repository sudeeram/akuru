import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.errors import DomainError
from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.official_paper_reviews import (
    CreateReviewCrop, PaperReviewResponse, ReviewCropResponse, SaveReviewQuestion, SeedPaperReview, StartPaperReview,
)
from app.schemas.worked_answers import GenerateWorkedAnswer, ReviewWorkedAnswer, GraphSolution, AttachWorkedAnswer
from app.services.worked_answers import lifecycle as worked_answers
from app.services.worked_answers.graphs import render as render_worked_graph
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


# Generated answers have independent provenance and approvals; never silently modify the question.


def _worked_enabled(settings):
    if not settings.worked_answers_enabled:
        raise DomainError("worked_answers_disabled", "AI-generated worked answers are not enabled.", 409)


@router.get('/{paper_id}/questions/{number}/worked-answers')
def list_worked_answers(paper_id: uuid.UUID, number: str,
    principal: Annotated[Principal, Depends(require_roles('admin'))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)]):
    return worked_answers.listing(db,paper_id,number)


@router.post('/{paper_id}/questions/{number}/worked-answers', status_code=202)
def generate_worked_answer(paper_id: uuid.UUID, number: str, payload: GenerateWorkedAnswer,
    principal: Annotated[Principal, Depends(require_csrf_roles('admin'))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)]):
    _worked_enabled(settings)
    if not worked_answers.capabilities(db,settings)['providerConfigured']:
        raise DomainError('worked_provider_unavailable','Configure an enabled OpenAI account and its server credential before generating.',409)
    return worked_answers.create(db,principal,paper_id,number,payload)


@router.post('/{paper_id}/questions/{number}/worked-answers/{answer_id}/review')
def review_worked_answer(paper_id: uuid.UUID, number: str, answer_id: uuid.UUID, payload: ReviewWorkedAnswer,
    principal: Annotated[Principal, Depends(require_csrf_roles('admin'))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)]):
    return worked_answers.review(db,principal,paper_id,number,answer_id,payload)


@router.get('/{paper_id}/questions/{number}/worked-answers/{answer_id}/steps/{step}/image')
def preview_worked_answer(paper_id: uuid.UUID, number: str, answer_id: uuid.UUID, step: int,
    principal: Annotated[Principal, Depends(require_roles('admin'))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)]):
    row=next((r for r in worked_answers.listing(db,paper_id,number) if r['id']==str(answer_id)),None)
    if not row or not row['solution'] or not 0 <= step < len(row['solution'].get('steps',[])):
        raise DomainError('worked_answer_not_found','Worked answer step not found.',404)
    return Response(render_worked_graph(GraphSolution.model_validate(row['solution']),step),media_type='image/png',
        headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})




@router.post('/{paper_id}/questions/{number}/worked-answers/{answer_id}/attach')
def attach_worked_answer(paper_id: uuid.UUID, number: str, answer_id: uuid.UUID, payload: AttachWorkedAnswer,
    principal: Annotated[Principal, Depends(require_csrf_roles('admin'))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)],
    storage: Annotated[ObjectStorage, Depends(get_storage)]):
    return worked_answers.attach(db,storage,principal,paper_id,number,answer_id,payload.expectedQuestionRevision)


@router.get('/{paper_id}/worked-answer-capabilities')
def worked_answer_capabilities(paper_id: uuid.UUID,
    principal: Annotated[Principal, Depends(require_roles('admin'))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)]):
    official_paper_reviews._workspace(db,paper_id)
    return worked_answers.capabilities(db,settings)
