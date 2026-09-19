from fastapi import APIRouter

from app.api.v1 import accounts, ai_accounts, assessments, auth, curriculum, documents, evaluations, flashcards, mastery, operations, questions, retrieval, study_plans, textbook_structures, tutoring, weaknesses, media


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(accounts.router)
api_router.include_router(ai_accounts.router)
api_router.include_router(curriculum.router)
api_router.include_router(documents.router)
api_router.include_router(textbook_structures.router)
api_router.include_router(questions.router)
api_router.include_router(assessments.router)
api_router.include_router(tutoring.router)
api_router.include_router(mastery.router)
api_router.include_router(weaknesses.router)
api_router.include_router(study_plans.router)
api_router.include_router(retrieval.router)
api_router.include_router(flashcards.router)
api_router.include_router(media.router)
api_router.include_router(evaluations.router)
api_router.include_router(operations.router)
