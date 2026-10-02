from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.permissions import require_roles
from app.schemas.student_textbooks import StudentTextbookList, StudentTextbookTopicContent
from app.security import Principal
from app.services import student_textbooks
from app.storage import ObjectStorage, get_storage


router = APIRouter(prefix="/student/textbooks", tags=["student textbooks"])


@router.get("", response_model=StudentTextbookList)
def list_textbooks(principal: Annotated[Principal, Depends(require_roles("student"))],
                   db: Annotated[Session, Depends(get_db)]):
    return student_textbooks.list_books(db, principal)


@router.get("/{book_ref}/topics/{topic_ref}", response_model=StudentTextbookTopicContent)
def read_topic(book_ref: str, topic_ref: str,
               principal: Annotated[Principal, Depends(require_roles("student"))],
               db: Annotated[Session, Depends(get_db)]):
    return student_textbooks.topic_content(db, principal, book_ref, topic_ref)


@router.get("/{book_ref}/topics/{topic_ref}/pages/{ordinal}/image")
def read_page_image(book_ref: str, topic_ref: str, ordinal: int,
                    principal: Annotated[Principal, Depends(require_roles("student"))],
                    db: Annotated[Session, Depends(get_db)],
                    storage: Annotated[ObjectStorage, Depends(get_storage)]):
    image = student_textbooks.page_image(db, storage, principal, book_ref, topic_ref, ordinal)
    return Response(content=image.content, media_type=image.content_type,
                    headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.get("/{book_ref}/topics/{topic_ref}/visuals/{asset_ref}")
def read_visual(book_ref: str, topic_ref: str, asset_ref: str,
                principal: Annotated[Principal, Depends(require_roles("student"))],
                db: Annotated[Session, Depends(get_db)],
                storage: Annotated[ObjectStorage, Depends(get_storage)]):
    image = student_textbooks.visual_image(db, storage, principal, book_ref, topic_ref, asset_ref)
    return Response(content=image.content, media_type=image.content_type,
                    headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})
