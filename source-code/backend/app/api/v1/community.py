from typing import Annotated, Literal
from fastapi import APIRouter, Depends, Query, Response, Path
from sqlalchemy.orm import Session
from app.database import get_db
from app.permissions import require_roles, require_csrf_roles
from app.security import Principal
from app.schemas.community import (CommunitySettingsDraft, CommunitySettings, CommunityPage,
    CommunityMember, CommunityFeed, NoticeRead, ReportDraft, ReportDecision,
    CommunityReports, CommunityResult, CommunitySubjectChoices)
from app.services import community as service


def private_response(response: Response):
    response.headers['Cache-Control'] = 'no-store'


router = APIRouter(prefix='/community', tags=['student community'], dependencies=[Depends(private_response)])
DB = Annotated[Session, Depends(get_db)]
Student = Annotated[Principal, Depends(require_roles('student'))]
StudentWrite = Annotated[Principal, Depends(require_csrf_roles('student'))]
Admin = Annotated[Principal, Depends(require_roles('admin'))]
AdminWrite = Annotated[Principal, Depends(require_csrf_roles('admin'))]
Page = Annotated[int, Query(ge=1, le=10000)]
Ref = Annotated[str, Path(pattern=r'^[a-z]+_[a-f0-9]{32}$', max_length=56)]


@router.get('/settings', response_model=CommunitySettings)
def settings(principal: Student, db: DB):
    return service.settings(db, principal.user.id)


@router.patch('/settings', response_model=CommunitySettings)
def save_settings(payload: CommunitySettingsDraft, principal: StudentWrite, db: DB):
    return service.save_settings(db, principal.user.id, payload)


@router.get('/subjects', response_model=CommunitySubjectChoices)
def subjects(principal: Student, db: DB, course: Annotated[str, Query(max_length=32)]):
    return service.course_subjects(db, principal.user.id, course)


@router.get('/members', response_model=CommunityPage)
def members(principal: Student, db: DB, kind: Literal['discover','following','followers']='discover',
    course: Annotated[str, Query(max_length=32)]='', subject: Annotated[str, Query(max_length=32)]='',
    q: Annotated[str, Query(max_length=64)]='', page: Page=1):
    return service.members(db, principal.user.id, kind, course, subject, q.strip(), page)


@router.get('/members/{ref}', response_model=CommunityMember)
def member(ref: Ref, principal: Student, db: DB):
    service.own(db, principal.user.id, participating=True)
    p = service.target(db, principal.user.id, ref)
    if not (service.course_ids(db, principal.user.id) & service.course_ids(db, p.student_id)) and not (service.connection(db, principal.user.id,p.student_id) or service.connection(db,p.student_id,principal.user.id)):
        from fastapi import HTTPException
        raise HTTPException(404, 'Community profile is unavailable.')
    return service.member(db, principal.user.id, p)


@router.post('/members/{ref}/follow', response_model=CommunityMember)
def follow(ref: Ref, principal: StudentWrite, db: DB):
    return service.follow(db, principal.user.id, ref)


@router.delete('/members/{ref}/follow', response_model=CommunityResult)
def unfollow(ref: Ref, principal: StudentWrite, db: DB):
    return service.unfollow(db, principal.user.id, ref)


@router.post('/members/{ref}/block', response_model=CommunityResult)
def block(ref: Ref, principal: StudentWrite, db: DB):
    return service.block(db, principal.user.id, ref)


@router.delete('/members/{ref}/block', response_model=CommunityResult)
def unblock(ref: Ref, principal: StudentWrite, db: DB):
    return service.block(db, principal.user.id, ref, remove=True)


@router.get('/blocks', response_model=CommunityPage)
def blocks(principal: Student, db: DB, page: Page=1):
    return service.blocks(db, principal.user.id, page)


@router.get('/feed', response_model=CommunityFeed)
def feed(principal: Student, db: DB, page: Page=1):
    return service.feed(db, principal.user.id, page)


@router.patch('/notifications/{ref}', response_model=CommunityResult)
def read_notice(ref: Ref, payload: NoticeRead, principal: StudentWrite, db: DB):
    return service.read_notice(db, principal.user.id, ref, payload.read)


@router.post('/members/{ref}/report', response_model=CommunityResult)
def report(ref: Ref, payload: ReportDraft, principal: StudentWrite, db: DB):
    return service.report(db, principal.user.id, ref, payload.reason)


@router.get('/reports', response_model=CommunityReports)
def reports(principal: Admin, db: DB, status: Literal['open','dismissed','name_change_required']='open', page: Page=1):
    return service.reports(db, status, page)


@router.patch('/reports/{ref}', response_model=CommunityResult)
def review(ref: Ref, payload: ReportDecision, principal: AdminWrite, db: DB):
    return service.review_report(db, principal.user.id, ref, payload.action)
