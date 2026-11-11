import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.errors import DomainError
from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.official_paper_reviews import (
    CreateReviewCrop, PaperAutoApprovalResponse, PaperReviewResponse, ReviewCropResponse, SaveReviewQuestion, SeedPaperReview, StartPaperReview,
)
from app.schemas.worked_answers import GenerateWorkedAnswer, ImportWorkedAnswerDraft, ReviewWorkedAnswer, parse_solution, AttachWorkedAnswer
from app.services.worked_answers import lifecycle as worked_answers
from app.services.worked_answers.graphs import render as render_worked_graph
from app.security import Principal
from app.services import official_paper_reviews
from app.storage import ObjectStorage, get_storage
from app.schemas.paper_analysis import RecordQuestionAnalysis, QuestionAnalysisResponse
from app.services import official_question_analyses


router = APIRouter(prefix="/admin/official-paper-reviews", tags=["official-paper-reviews"])

from app.schemas.evidence_links import ProposeEvidenceLinks, ReviewEvidenceLinks, EvidenceBatch
from app.services import evidence_links
from app.services import evidence_link_jobs


from app.schemas.accuracy_jobs import AccuracyJobBatch
from app.services import accuracy_jobs

@router.get('/{paper_id}/accuracy-readiness')
def accuracy_readiness(paper_id: uuid.UUID, principal: Annotated[Principal, Depends(require_roles('admin'))], db: Annotated[Session, Depends(get_db)]):
    return accuracy_jobs.readiness(db,paper_id)

@router.get('/{paper_id}/accuracy-jobs')
def accuracy_job_status(paper_id: uuid.UUID, principal: Annotated[Principal, Depends(require_roles('admin'))], db: Annotated[Session, Depends(get_db)]):
    return accuracy_jobs.listing(db,paper_id)

@router.post('/{paper_id}/accuracy-jobs',status_code=202)
def queue_accuracy_jobs(paper_id: uuid.UUID, payload: AccuracyJobBatch, principal: Annotated[Principal, Depends(require_csrf_roles('admin'))], db: Annotated[Session, Depends(get_db)]):
    return accuracy_jobs.create_batch(db,principal,paper_id,payload)


@router.get('/{paper_id}/evidence-link-jobs')
def evidence_jobs(paper_id: uuid.UUID,
    principal: Annotated[Principal, Depends(require_roles('admin'))],
    db: Annotated[Session, Depends(get_db)]):
    return evidence_link_jobs.listing(db, paper_id)


@router.post('/{paper_id}/evidence-link-jobs', status_code=202)
def create_evidence_job(paper_id: uuid.UUID, payload: ProposeEvidenceLinks,
    principal: Annotated[Principal, Depends(require_csrf_roles('admin'))],
    db: Annotated[Session, Depends(get_db)]):
    return evidence_link_jobs.create(db, principal, paper_id, payload)


@router.post('/{paper_id}/evidence-link-job-batch', status_code=202)
def create_evidence_job_batch(paper_id: uuid.UUID, payload: EvidenceBatch,
    principal: Annotated[Principal, Depends(require_csrf_roles('admin'))],
    db: Annotated[Session, Depends(get_db)]):
    return evidence_link_jobs.create_batch(db, principal, paper_id, payload)


@router.get('/{paper_id}/evidence-links/{run_id}/{proposal_id}/preview')
def evidence_link_preview(paper_id: uuid.UUID, run_id: uuid.UUID, proposal_id: uuid.UUID,
    principal: Annotated[Principal, Depends(require_roles('admin'))],
    db: Annotated[Session, Depends(get_db)], storage: Annotated[ObjectStorage, Depends(get_storage)]):
    return Response(evidence_links.preview(db, storage, paper_id, run_id, proposal_id), media_type='image/png',
        headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})


@router.get('/{paper_id}/evidence-links')
def evidence_link_runs(paper_id: uuid.UUID,
    principal: Annotated[Principal, Depends(require_roles('admin'))],
    db: Annotated[Session, Depends(get_db)]):
    return evidence_links.listing(db, paper_id)


@router.post('/{paper_id}/evidence-links')
def propose_evidence_links(paper_id: uuid.UUID, payload: ProposeEvidenceLinks,
    principal: Annotated[Principal, Depends(require_csrf_roles('admin'))],
    db: Annotated[Session, Depends(get_db)], storage: Annotated[ObjectStorage, Depends(get_storage)]):
    return evidence_links.propose(db, storage, principal, paper_id, payload)


@router.post('/{paper_id}/evidence-links/{run_id}/review')
def review_evidence_links(paper_id: uuid.UUID, run_id: uuid.UUID, payload: ReviewEvidenceLinks,
    principal: Annotated[Principal, Depends(require_csrf_roles('admin'))],
    db: Annotated[Session, Depends(get_db)], storage: Annotated[ObjectStorage, Depends(get_storage)]):
    return evidence_links.decide(db, storage, principal, paper_id, run_id, payload)


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


@router.get("/{paper_id}/questions/{number}/analyses", response_model=list[QuestionAnalysisResponse])
def analysis_history(paper_id: uuid.UUID, number: str,
    principal: Annotated[Principal, Depends(require_roles("admin"))],
    db: Annotated[Session, Depends(get_db)]):
    return official_question_analyses.history(db, paper_id, number)


@router.post("/{paper_id}/questions/{number}/analyses", response_model=QuestionAnalysisResponse, status_code=201)
def record_analysis(paper_id: uuid.UUID, number: str, payload: RecordQuestionAnalysis,
    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
    db: Annotated[Session, Depends(get_db)]):
    return official_question_analyses.record(db, principal, paper_id, number, payload)


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


@router.post('/{paper_id}/questions/{number}/worked-answers/import-draft', status_code=201)
def import_worked_answer_draft(paper_id: uuid.UUID, number: str, payload: ImportWorkedAnswerDraft,
    principal: Annotated[Principal, Depends(require_csrf_roles('admin'))],
    db: Annotated[Session, Depends(get_db)]):
    return worked_answers.import_draft(db,principal,paper_id,number,payload)


@router.post('/{paper_id}/questions/{number}/worked-answers/{answer_id}/review')
def review_worked_answer(paper_id: uuid.UUID, number: str, answer_id: uuid.UUID, payload: ReviewWorkedAnswer,
    principal: Annotated[Principal, Depends(require_csrf_roles('admin'))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)],
    storage: Annotated[ObjectStorage, Depends(get_storage)]):
    return worked_answers.review(db,storage,principal,paper_id,number,answer_id,payload)


@router.get('/{paper_id}/questions/{number}/worked-answers/{answer_id}/steps/{step}/image')
def preview_worked_answer(paper_id: uuid.UUID, number: str, answer_id: uuid.UUID, step: int,
    principal: Annotated[Principal, Depends(require_roles('admin'))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)]):
    row=next((r for r in worked_answers.listing(db,paper_id,number) if r['id']==str(answer_id)),None)
    if not row or not row['solution'] or not 0 <= step < len(row['solution'].get('steps',[])):
        raise DomainError('worked_answer_not_found','Worked answer step not found.',404)
    return Response(render_worked_graph(parse_solution(row['solution']),step),media_type='image/png',
        headers={'Cache-Control':'private, no-store','X-Content-Type-Options':'nosniff'})




@router.post('/{paper_id}/questions/{number}/worked-answers/{answer_id}/attach')
def attach_worked_answer(paper_id: uuid.UUID, number: str, answer_id: uuid.UUID, payload: AttachWorkedAnswer,
    principal: Annotated[Principal, Depends(require_csrf_roles('admin'))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)],
    storage: Annotated[ObjectStorage, Depends(get_storage)]):
    return worked_answers.attach(db,storage,principal,paper_id,number,answer_id,payload.expectedQuestionRevision,
        reopen_approved=payload.reopenApproved)


@router.get('/{paper_id}/worked-answer-capabilities')
def worked_answer_capabilities(paper_id: uuid.UUID,
    principal: Annotated[Principal, Depends(require_roles('admin'))],
    db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)]):
    official_paper_reviews._workspace(db,paper_id)
    return worked_answers.capabilities(db,settings)


@router.get("/{paper_id}/chat-releases")
def chat_releases(paper_id: uuid.UUID,
    _principal: Annotated[Principal, Depends(require_roles("admin"))],
    db: Annotated[Session, Depends(get_db)]):
    from app.services import tutor_past_papers
    return tutor_past_papers.admin_releases(db, paper_id)


from app.schemas.tutor_past_papers import ReleasePastPaperPart


@router.post("/{paper_id}/questions/{number}/chat-release")
def release_chat_part(paper_id: uuid.UUID, number: str, payload: ReleasePastPaperPart,
    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
    db: Annotated[Session, Depends(get_db)]):
    from app.services import tutor_past_papers
    return tutor_past_papers.release_part(db, principal, paper_id, number, payload)


@router.post("/{paper_id}/auto-approval", response_model=PaperAutoApprovalResponse)
def apply_confidence_approval(paper_id: uuid.UUID,
    principal: Annotated[Principal, Depends(require_csrf_roles("admin"))],
    db: Annotated[Session, Depends(get_db)]):
    from app.services.question_auto_approval import apply_paper
    return apply_paper(db, principal, paper_id)
