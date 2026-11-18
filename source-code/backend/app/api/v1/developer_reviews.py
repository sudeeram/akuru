"""Admin-only model-free review orchestration. All writes retain CSRF checks."""
import uuid
from typing import Annotated
from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.permissions import require_roles,require_csrf_roles
from app.security import Principal
from app.schemas.developer_reviews import StageReview,ApplyReview,ScopedApproval,ReleaseValidation,ReviewBatch
from app.services import developer_reviews as service

router=APIRouter(prefix='/admin/official-paper-reviews',tags=['developer-reviews'])
Admin=Annotated[Principal,Depends(require_roles('admin'))]
Writer=Annotated[Principal,Depends(require_csrf_roles('admin'))]
DB=Annotated[Session,Depends(get_db)]

@router.get('/{paper_id}/readiness')
def readiness(paper_id:uuid.UUID,principal:Admin,db:DB):
    return service.readiness(db,paper_id)

@router.get('/{paper_id}/review-package')
def package(paper_id:uuid.UUID,principal:Admin,db:DB,number:Annotated[list[str]|None,Query(max_length=100)]=None,offset:int=Query(default=0,ge=0),limit:int=Query(default=10,ge=1,le=20)):
    return service.export_package(db,paper_id,number,offset,limit)

@router.post('/{paper_id}/change-sets',status_code=201)
def stage(paper_id:uuid.UUID,payload:StageReview,principal:Writer,db:DB):
    return service.stage(db,principal,paper_id,payload)

@router.get('/{paper_id}/change-sets/{change_set_id}')
def get(paper_id:uuid.UUID,change_set_id:uuid.UUID,principal:Admin,db:DB):
    return service.change_set(db,paper_id,change_set_id)

@router.get('/{paper_id}/change-sets/{change_set_id}/preview')
def preview(paper_id:uuid.UUID,change_set_id:uuid.UUID,principal:Admin,db:DB):
    return service.preview(db,paper_id,change_set_id)

@router.post('/{paper_id}/change-sets/{change_set_id}/apply')
def apply(paper_id:uuid.UUID,change_set_id:uuid.UUID,payload:ApplyReview,principal:Writer,db:DB):
    return service.apply(db,principal,paper_id,change_set_id,payload)

@router.post('/{paper_id}/questions/{number}/auto-approval')
def approve(paper_id:uuid.UUID,number:str,payload:ScopedApproval,principal:Writer,db:DB):
    return service.approve(db,principal,paper_id,number,payload)

@router.post('/{paper_id}/release-validation')
def release_validation(paper_id:uuid.UUID,payload:ReleaseValidation,principal:Writer,db:DB):
    return service.validate_release(db,paper_id,payload)

@router.get('/{paper_id}/review-history')
def history(paper_id:uuid.UUID,principal:Admin,db:DB,limit:int=Query(default=50,ge=1,le=100),offset:int=Query(default=0,ge=0)):
    return service.history(db,paper_id,limit,offset)

@router.post('/{paper_id}/review-batches',status_code=201)
def batch(paper_id:uuid.UUID,payload:ReviewBatch,principal:Writer,db:DB):
    return service.run_batch(db,principal,paper_id,payload)

@router.get('/{paper_id}/review-batches/{batch_id}')
def batch_get(paper_id:uuid.UUID,batch_id:uuid.UUID,principal:Admin,db:DB):
    return service.batch_status(db,paper_id,batch_id)

@router.post('/{paper_id}/review-batches/{batch_id}/resume')
def resume(paper_id:uuid.UUID,batch_id:uuid.UUID,payload:ReviewBatch,principal:Writer,db:DB):
    if batch_id!=payload.requestId:
        from app.errors import DomainError
        raise DomainError('review_batch_mismatch','Batch identity does not match.',409)
    return service.run_batch(db,principal,paper_id,payload,resume=True)
