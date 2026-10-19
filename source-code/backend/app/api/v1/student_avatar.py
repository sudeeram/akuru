from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditEvent, StudentProfile
from app.permissions import require_csrf_roles, require_roles
from app.schemas.student_avatar import StudentAvatarConfig, StudentAvatarResponse, public_avatar
from app.security import Principal

router = APIRouter(prefix='/student/avatar', tags=['student avatar'])


def own_profile(db: Session, principal: Principal) -> StudentProfile:
    profile = db.get(StudentProfile, principal.user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail='Student profile is not available.')
    return profile


@router.get('', response_model=StudentAvatarResponse)
def get_avatar(response: Response, principal: Annotated[Principal, Depends(require_roles('student'))], db: Annotated[Session, Depends(get_db)]):
    response.headers['Cache-Control'] = 'no-store'
    return {'avatar': public_avatar(own_profile(db, principal).avatar_config)}


def persist(db: Session, principal: Principal, avatar: dict | None):
    profile = own_profile(db, principal)
    profile.avatar_config = avatar
    db.add(AuditEvent(actor_id=principal.user.id, action='student.avatar.saved' if avatar else 'student.avatar.reset', target_type='student_profile', target_id=str(principal.user.id), event_data={'version': 1}))
    db.commit()
    return {'avatar': public_avatar(profile.avatar_config)}


@router.patch('', response_model=StudentAvatarResponse)
def save_avatar(payload: StudentAvatarConfig, response: Response, principal: Annotated[Principal, Depends(require_csrf_roles('student'))], db: Annotated[Session, Depends(get_db)]):
    response.headers['Cache-Control'] = 'no-store'
    return persist(db, principal, payload.model_dump())


@router.delete('', response_model=StudentAvatarResponse)
def reset_avatar(response: Response, principal: Annotated[Principal, Depends(require_csrf_roles('student'))], db: Annotated[Session, Depends(get_db)]):
    response.headers['Cache-Control'] = 'no-store'
    return persist(db, principal, None)
