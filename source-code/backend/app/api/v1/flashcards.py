from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.flashcards import (FlashcardCardUpdateRequest, FlashcardDeckResponse,
    FlashcardGenerateRequest, FlashcardRatingRequest, FlashcardSessionResponse,
    FlashcardSessionStartRequest)
from app.security import Principal
from app.services import flashcards

router = APIRouter(prefix="/flashcards", tags=["flashcards"])

@router.get("/admin/decks", response_model=list[FlashcardDeckResponse])
def admin_list(_p: Annotated[Principal, Depends(require_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.admin_list(db)

@router.get("/admin/decks/{deck_ref}", response_model=FlashcardDeckResponse)
def admin_get(deck_ref: str, _p: Annotated[Principal, Depends(require_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.admin_get(db, deck_ref)

@router.post("/admin/decks/generate", response_model=FlashcardDeckResponse)
def generate(payload: FlashcardGenerateRequest, p: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.generate(db, p, payload.topicRef, payload.cardLimit, payload.requestKey)

@router.patch("/admin/decks/{deck_ref}/cards/{card_ref}", response_model=FlashcardDeckResponse)
def review(deck_ref: str, card_ref: str, payload: FlashcardCardUpdateRequest,
           p: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.review_card(db, p, deck_ref, card_ref, payload.front, payload.back, payload.decision)

@router.post("/admin/decks/{deck_ref}/release", response_model=FlashcardDeckResponse)
def release(deck_ref: str, p: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.release(db, p, deck_ref)

@router.get("/student/decks", response_model=list[FlashcardDeckResponse])
def decks(p: Annotated[Principal, Depends(require_roles("student"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.student_decks(db, p)

@router.post("/student/decks/{deck_ref}/sessions", response_model=FlashcardSessionResponse)
def start(deck_ref: str, payload: FlashcardSessionStartRequest,
          p: Annotated[Principal, Depends(require_csrf_roles("student"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.start_session(db, p, deck_ref, payload.requestKey)

@router.get("/student/sessions/{session_ref}", response_model=FlashcardSessionResponse)
def session(session_ref: str, p: Annotated[Principal, Depends(require_roles("student"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.get_session(db, p, session_ref)

@router.post("/student/sessions/{session_ref}/reveal", response_model=FlashcardSessionResponse)
def reveal(session_ref: str, p: Annotated[Principal, Depends(require_csrf_roles("student"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.get_session(db, p, session_ref, reveal=True)

@router.post("/student/sessions/{session_ref}/rate", response_model=FlashcardSessionResponse)
def rate(session_ref: str, payload: FlashcardRatingRequest,
         p: Annotated[Principal, Depends(require_csrf_roles("student"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.rate(db, p, session_ref, payload.rating, payload.requestKey)
