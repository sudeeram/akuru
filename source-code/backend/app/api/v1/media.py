import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session
from app.config import Settings, get_settings
from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.media import DeterministicMediaCreate, IllustrationCreate, MediaListResponse, MediaResponse, MediaReview, MediaSourceResponse
from app.security import Principal
from app.services import media
from app.storage import ObjectStorage, get_storage

router=APIRouter(prefix="/media",tags=["media"])

@router.get("/admin/sources",response_model=list[MediaSourceResponse])
def source_options(subject_id:Annotated[str,Query(alias="subjectId")],_principal:Annotated[Principal,Depends(require_roles("admin"))],
                   db:Annotated[Session,Depends(get_db)]): return media.sources(db,subject_id)

@router.get("",response_model=MediaListResponse)
def list_rows(principal:Annotated[Principal,Depends(require_roles("admin","parent","student"))],
              db:Annotated[Session,Depends(get_db)],student_id:Annotated[uuid.UUID|None,Query(alias="studentId")]=None,
              subject_id:Annotated[str|None,Query(alias="subjectId")]=None):
    return media.list_media(db,principal,student_id,subject_id)

@router.post("/admin/deterministic",response_model=MediaResponse,status_code=status.HTTP_201_CREATED)
def create_deterministic(payload:DeterministicMediaCreate,principal:Annotated[Principal,Depends(require_csrf_roles("admin"))],
                         db:Annotated[Session,Depends(get_db)],storage:Annotated[ObjectStorage,Depends(get_storage)]):
    return media.deterministic(db,storage,principal,payload)

@router.post("/admin/illustrations",response_model=MediaResponse,status_code=status.HTTP_201_CREATED)
def create_illustration(payload:IllustrationCreate,principal:Annotated[Principal,Depends(require_csrf_roles("admin"))],
                        db:Annotated[Session,Depends(get_db)],settings:Annotated[Settings,Depends(get_settings)],
                        storage:Annotated[ObjectStorage,Depends(get_storage)]):
    return media.illustration(db,storage,settings,principal,payload)

@router.post("/admin/{media_id}/review",response_model=MediaResponse)
def review(media_id:uuid.UUID,payload:MediaReview,principal:Annotated[Principal,Depends(require_csrf_roles("admin"))],
           db:Annotated[Session,Depends(get_db)]): return media.review(db,principal,media_id,payload)

@router.get("/{media_id}/content")
def get_content(media_id:uuid.UUID,principal:Annotated[Principal,Depends(require_roles("admin","parent","student"))],
                db:Annotated[Session,Depends(get_db)],storage:Annotated[ObjectStorage,Depends(get_storage)],
                student_id:Annotated[uuid.UUID|None,Query(alias="studentId")]=None):
    stored=media.content(db,storage,principal,media_id,student_id)
    return Response(content=stored.content,media_type=stored.content_type,
        headers={"Cache-Control":"private, no-store","X-Content-Type-Options":"nosniff",
                 "Content-Security-Policy":"default-src 'none'; style-src 'unsafe-inline'"})
