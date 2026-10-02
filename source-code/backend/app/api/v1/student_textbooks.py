from typing import Annotated
from io import BytesIO

from fastapi import APIRouter, Depends, Response
from PIL import Image
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


@router.get("/{book_ref}/topics/{topic_ref}/visual-references/{source_ordinal}/pages/{page_ordinal}/image")
def read_visual_reference_page(book_ref: str, topic_ref: str, source_ordinal: int, page_ordinal: int,
                               principal: Annotated[Principal, Depends(require_roles("student"))],
                               db: Annotated[Session, Depends(get_db)],
                               storage: Annotated[ObjectStorage, Depends(get_storage)]):
    image = student_textbooks.reference_page_image(db, storage, principal, book_ref, topic_ref,
                                                    source_ordinal, page_ordinal)
    return Response(content=image.content, media_type=image.content_type,
                    headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.get("/{book_ref}/topics/{topic_ref}/visual-references/{source_ordinal}/pages/{page_ordinal}/thumbnail")
def read_visual_reference_thumbnail(book_ref: str, topic_ref: str, source_ordinal: int, page_ordinal: int,
                                    principal: Annotated[Principal, Depends(require_roles("student"))],
                                    db: Annotated[Session, Depends(get_db)],
                                    storage: Annotated[ObjectStorage, Depends(get_storage)]):
    original = student_textbooks.reference_page_image(db, storage, principal, book_ref, topic_ref,
                                                       source_ordinal, page_ordinal)
    with Image.open(BytesIO(original.content)) as page:
        page.thumbnail((220, 300))
        output = BytesIO()
        page.convert("RGB").save(output, format="JPEG", quality=72, optimize=True)
    return Response(content=output.getvalue(), media_type="image/jpeg",
                    headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})
