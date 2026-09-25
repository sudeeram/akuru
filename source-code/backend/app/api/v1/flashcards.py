from typing import Annotated

import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.flashcards import (FlashcardDeckResponse, FlashcardDiscardResponse,
    FlashcardMasteryResponse, FlashcardRatingRequest, FlashcardSessionResponse,
    FlashcardSessionStartRequest, FlashcardStudyOptionsResponse, FlashcardWithdrawRequest)
from app.security import Principal
from app.services import flashcards
from app.storage.base import ObjectStorage
from app.storage.factory import get_storage

router = APIRouter(prefix="/flashcards", tags=["flashcards"])

@router.get("/admin/decks", response_model=list[FlashcardDeckResponse])
def admin_list(_p: Annotated[Principal, Depends(require_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.admin_list(db)

@router.get("/admin/decks/{deck_ref}", response_model=FlashcardDeckResponse)
def admin_get(deck_ref: str, _p: Annotated[Principal, Depends(require_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.admin_get(db, deck_ref)

@router.post("/admin/decks/{deck_ref}/withdraw", response_model=FlashcardDeckResponse)
def withdraw(deck_ref: str, payload: FlashcardWithdrawRequest,
             p: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.withdraw(db, p, deck_ref, payload.reason)

@router.get("/student/decks", response_model=list[FlashcardDeckResponse])
def decks(p: Annotated[Principal, Depends(require_roles("student"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.student_decks(db, p)

@router.post("/student/decks/{deck_ref}/sessions", response_model=FlashcardSessionResponse)
def start(deck_ref: str, payload: FlashcardSessionStartRequest,
          p: Annotated[Principal, Depends(require_csrf_roles("student"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.start_session(db, p, deck_ref, payload.requestKey, payload.mode,
                                    payload.difficulty, payload.requestedCount)

@router.get("/student/decks/{deck_ref}/study-options", response_model=FlashcardStudyOptionsResponse)
def options(deck_ref: str, p: Annotated[Principal, Depends(require_roles("student"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.study_options(db, p, deck_ref)

@router.get("/student/decks/{deck_ref}/mastery", response_model=FlashcardMasteryResponse)
def mastery(deck_ref: str, p: Annotated[Principal, Depends(require_roles("student"))],
            db: Annotated[Session, Depends(get_db)]):
    return flashcards.mastery_summary(db, p, deck_ref)

@router.get("/student/sessions/{session_ref}", response_model=FlashcardSessionResponse)
def session(session_ref: str, p: Annotated[Principal, Depends(require_roles("student"))],
            db: Annotated[Session, Depends(get_db)], position: int | None = Query(default=None, ge=1)):
    return flashcards.get_session(db, p, session_ref, position)

@router.post("/student/sessions/{session_ref}/reveal", response_model=FlashcardSessionResponse)
def reveal(session_ref: str, p: Annotated[Principal, Depends(require_csrf_roles("student"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.reveal(db, p, session_ref)

@router.post("/student/sessions/{session_ref}/discard", response_model=FlashcardDiscardResponse)
def discard(session_ref: str,
            p: Annotated[Principal, Depends(require_csrf_roles("student"))],
            db: Annotated[Session, Depends(get_db)]):
    return flashcards.discard(db, p, session_ref)

@router.get("/student/sessions/{session_ref}/visuals/{visual_ref}")
def visual(session_ref: str, visual_ref: str,
           p: Annotated[Principal, Depends(require_roles("student"))],
           db: Annotated[Session, Depends(get_db)],
           storage: Annotated[ObjectStorage, Depends(get_storage)]) -> Response:
    stored = flashcards.open_visual(db, p, storage, session_ref, visual_ref)
    return Response(content=stored.content, media_type=stored.content_type,
                    headers={"Cache-Control": "private, no-store", "Vary": "Cookie",
                             "X-Content-Type-Options": "nosniff"})

@router.get("/student/sessions/{session_ref}/textbook-pages/{page_id}")
def textbook_page(session_ref: str, page_id: uuid.UUID,
                  p: Annotated[Principal, Depends(require_roles("student"))],
                  db: Annotated[Session, Depends(get_db)],
                  storage: Annotated[ObjectStorage, Depends(get_storage)]) -> Response:
    stored = flashcards.open_textbook_page(db, p, storage, session_ref, page_id)
    return Response(content=stored.content, media_type=stored.content_type,
                    headers={"Cache-Control": "private, no-store", "Vary": "Cookie",
                             "X-Content-Type-Options": "nosniff"})

@router.post("/student/sessions/{session_ref}/rate", response_model=FlashcardSessionResponse)
def rate(session_ref: str, payload: FlashcardRatingRequest,
         p: Annotated[Principal, Depends(require_csrf_roles("student"))], db: Annotated[Session, Depends(get_db)]):
    return flashcards.rate(db, p, session_ref, payload.rating, payload.requestKey)
