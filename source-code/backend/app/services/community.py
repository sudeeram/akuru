"""Course-scoped discovery, independent follows and privacy-filtered events."""
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy import and_, delete, exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models import (AuditEvent, CommunityBlock as Block, CommunityFollow as Follow,
    CommunityNotification as Notice, CommunityProfile as Profile, CommunityReport as Report,
    Course, StudentProfile, StudentProgression, StudentSubject, Subject, User)
from app.schemas.student_avatar import public_avatar

PAGE_SIZE = 20


def now():
    return datetime.now(timezone.utc)


def utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def own(db, actor, *, participating=False):
    profile = db.get(Profile, actor)
    if not profile:
        if not db.get(StudentProfile, actor):
            raise HTTPException(404, 'Student profile is unavailable.')
        if participating:
            raise HTTPException(403, 'Enable your community profile first.')
        return None
    if participating and (not profile.enabled or profile.name_change_required):
        raise HTTPException(403, 'Enable your community profile with an approved public name first.')
    return profile


def course_ids(db, actor):
    return set(db.scalars(select(StudentProgression.course_id).where(
        StudentProgression.student_id == actor, StudentProgression.is_current.is_(True))))


def subjects(db, actor):
    return list(db.scalars(select(Subject).join(StudentSubject, StudentSubject.subject_id == Subject.id)
        .where(StudentSubject.student_id == actor).order_by(Subject.name)))


def choices(rows):
    return [{'id': row.id, 'name': row.name} for row in rows]


def settings(db, actor):
    p = own(db, actor)
    enrolled = subjects(db, actor)
    return {'publicName': p.public_name if p else '', 'enabled': p.enabled if p else False,
        'visibleSubjectIds': [s.id for s in enrolled if p and s.id in p.visible_subject_ids],
        'nameChangeRequired': p.name_change_required if p else False,
        'courses': choices(db.scalars(select(Course).where(Course.id.in_(course_ids(db, actor))).order_by(Course.name))),
        'subjects': choices(enrolled)}


def lock(db, *actors):
    # All pair mutations acquire the same ordered locks, including block and report.
    # User rows also exist before the first community preference is saved.
    list(db.scalars(select(User).where(User.id.in_(set(actors))).order_by(User.id).with_for_update()))
    db.expire_all()


def throttle(profile):
    stamp = now()
    if not profile.action_window or utc(profile.action_window) < stamp - timedelta(minutes=1):
        profile.action_window, profile.action_count = stamp, 0
    if profile.action_count >= 30:
        raise HTTPException(429, 'Please wait a minute before making more community changes.')
    profile.action_count += 1


def audit(db, actor, action, ref):
    db.add(AuditEvent(actor_id=actor, action=action, target_type='community', target_id=ref, event_data={}))


def save_settings(db, actor, draft):
    lock(db, actor)
    profile = own(db, actor)
    if profile is None:
        profile = Profile(student_id=actor, visible_subject_ids=[], action_count=0)
        db.add(profile)
    throttle(profile)
    key = draft.publicName.casefold()
    if profile.name_change_required and key == profile.name_key and draft.enabled:
        raise HTTPException(422, 'Choose a different public name before rejoining.')
    valid_subjects = {s.id for s in subjects(db, actor)}
    if not set(draft.visibleSubjectIds) <= valid_subjects:
        raise HTTPException(422, 'Only your enrolled subjects can be displayed.')
    if profile.name_change_required and key != profile.name_key:
        profile.name_change_required = False
    profile.public_name, profile.name_key = draft.publicName, key
    profile.enabled = draft.enabled and not profile.name_change_required
    profile.visible_subject_ids = sorted(set(draft.visibleSubjectIds))
    try:
        db.flush()
        audit(db, actor, 'community.settings.saved', profile.public_ref)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'That public name is taken. Please choose another.')
    return settings(db, actor)


def blocked_clause(actor, target):
    return exists(select(Block.blocker_id).where(or_(
        and_(Block.blocker_id == actor, Block.blocked_id == target),
        and_(Block.blocked_id == actor, Block.blocker_id == target))))


def visible_query(actor):
    return select(Profile).join(User, User.id == Profile.student_id).where(
        User.is_active.is_(True), User.role == 'student', Profile.enabled.is_(True),
        Profile.name_change_required.is_(False), Profile.student_id != actor,
        ~blocked_clause(actor, Profile.student_id))


def connection(db, first, second):
    return db.get(Follow, (first, second)) is not None


def member(db, actor, profile):
    student = db.get(StudentProfile, profile.student_id)
    return {'ref': profile.public_ref, 'publicName': profile.public_name,
        'avatar': public_avatar(student.avatar_config) if student else None,
        'subjects': choices([s for s in subjects(db, profile.student_id) if s.id in profile.visible_subject_ids]),
        'following': connection(db, actor, profile.student_id),
        'followsYou': connection(db, profile.student_id, actor)}


def target(db, actor, ref, *, eligible=True):
    query = visible_query(actor) if eligible else select(Profile).where(Profile.student_id != actor)
    p = db.scalar(query.where(Profile.public_ref == ref))
    if p is None:
        raise HTTPException(404, 'Community profile is unavailable.')
    return p


def validate_course(db, actor, course):
    if course not in course_ids(db, actor):
        raise HTTPException(403, 'Choose one of your current courses.')


def course_subjects(db, actor, course):
    own(db, actor, participating=True)
    validate_course(db, actor, course)
    # Subjects are globally catalogued today, assigned to the current course via
    # Student enrolment. Offer only subjects actually enrolled within that course.
    participants = visible_query(actor).where(Profile.student_id.in_(
        select(StudentProgression.student_id).where(StudentProgression.course_id == course,
            StudentProgression.is_current.is_(True))))
    public_subjects = select(StudentSubject.subject_id).join(Profile,
        Profile.student_id == StudentSubject.student_id).where(
        Profile.student_id.in_(participants.with_only_columns(Profile.student_id)))
    if db.bind.dialect.name == 'postgresql':
        from sqlalchemy import cast
        from sqlalchemy.dialects.postgresql import JSONB
        public_subjects = public_subjects.where(cast(Profile.visible_subject_ids, JSONB).contains(func.jsonb_build_array(StudentSubject.subject_id)))
    else:
        from sqlalchemy import text
        public_subjects = public_subjects.where(text('EXISTS (SELECT 1 FROM json_each(community_profiles.visible_subject_ids) WHERE value = student_subjects.subject_id)'))
    own_subjects = select(StudentSubject.subject_id).where(StudentSubject.student_id == actor)
    return {'subjects': choices(db.scalars(select(Subject).where(
        or_(Subject.id.in_(public_subjects), Subject.id.in_(own_subjects))).order_by(Subject.name)))}



def members(db, actor, kind, course, subject, search, page):
    own(db, actor, participating=True)
    query = visible_query(actor)
    if kind == 'discover':
        validate_course(db, actor, course)
        query = query.where(Profile.student_id.in_(select(StudentProgression.student_id).where(
            StudentProgression.course_id == course, StudentProgression.is_current.is_(True))))
        if subject:
            query = query.where(Profile.student_id.in_(select(StudentSubject.student_id).where(StudentSubject.subject_id == subject)))
            # JSON portability: enrolment visibility is checked in SQL on Postgres
            # through the common JSON array containment function below via EXISTS.
            if db.bind.dialect.name == 'postgresql':
                from sqlalchemy import cast
                from sqlalchemy.dialects.postgresql import JSONB
                query = query.where(cast(Profile.visible_subject_ids, JSONB).contains([subject]))
            else:
                from sqlalchemy import text
                query = query.where(text('EXISTS (SELECT 1 FROM json_each(community_profiles.visible_subject_ids) WHERE value = :visible_subject)').bindparams(visible_subject=subject))
    elif kind == 'following':
        query = query.where(Profile.student_id.in_(select(Follow.followed_id).where(Follow.follower_id == actor)))
    else:
        query = query.where(Profile.student_id.in_(select(Follow.follower_id).where(Follow.followed_id == actor)))
    if search:
        query = query.where(func.lower(Profile.public_name).contains(search.lower(), autoescape=True))
    rows = list(db.scalars(query.order_by(func.lower(Profile.public_name), Profile.public_ref).offset((page-1)*PAGE_SIZE).limit(PAGE_SIZE+1)))
    return {'members': [member(db, actor, p) for p in rows[:PAGE_SIZE]], 'hasMore': len(rows)>PAGE_SIZE, 'page': page}


def follow(db, actor, ref):
    p = target(db, actor, ref)
    lock(db, actor, p.student_id)
    me = own(db, actor, participating=True)
    p = target(db, actor, ref)  # Revalidate after locks (hide/block may have won).
    if not (course_ids(db, actor) & course_ids(db, p.student_id)) and not connection(db, p.student_id, actor):
        raise HTTPException(403, 'New connections must share a current course.')
    if not connection(db, actor, p.student_id):
        throttle(me)
        db.add(Follow(follower_id=actor, followed_id=p.student_id))
        notice = db.scalar(select(Notice).where(Notice.recipient_id == p.student_id, Notice.actor_id == actor, Notice.event_type == 'follow.v1'))
        if notice is None:
            db.add(Notice(recipient_id=p.student_id, actor_id=actor, event_type='follow.v1', created_at=now(), read=False))
        elif utc(notice.created_at) < now() - timedelta(hours=24):
            notice.created_at, notice.read = now(), False
        audit(db, actor, 'community.follow', ref)
    db.commit()
    return member(db, actor, p)


def unfollow(db, actor, ref):
    p = target(db, actor, ref, eligible=False)
    lock(db, actor, p.student_id)
    me = own(db, actor, participating=True)
    throttle(me)
    db.execute(delete(Follow).where(Follow.follower_id == actor, Follow.followed_id == p.student_id))
    db.commit()
    return {'ok': True}


def block(db, actor, ref, remove=False):
    # Existing outgoing blocks may be undone even while one's profile is hidden.
    p = target(db, actor, ref, eligible=False)
    lock(db, actor, p.student_id)
    me = own(db, actor, participating=not remove)
    if me is None:
        raise HTTPException(404, 'Community profile is unavailable.')
    throttle(me)
    existing = db.get(Block, (actor, p.student_id))
    if remove:
        if existing: db.delete(existing)
    else:
        if not existing:
            target(db, actor, ref)
            db.add(Block(blocker_id=actor, blocked_id=p.student_id))
        pair = or_(and_(Follow.follower_id == actor, Follow.followed_id == p.student_id), and_(Follow.followed_id == actor, Follow.follower_id == p.student_id))
        db.execute(delete(Follow).where(pair))
        db.execute(delete(Notice).where(or_(and_(Notice.actor_id == actor, Notice.recipient_id == p.student_id), and_(Notice.recipient_id == actor, Notice.actor_id == p.student_id))))
    audit(db, actor, 'community.unblock' if remove else 'community.block', ref)
    db.commit()
    return {'ok': True}


def blocks(db, actor, page):
    own(db, actor)
    rows = list(db.scalars(select(Profile).join(Block, Block.blocked_id == Profile.student_id).where(Block.blocker_id == actor).order_by(Profile.public_ref).offset((page-1)*PAGE_SIZE).limit(PAGE_SIZE+1)))
    # Saved blocks are manageable without revealing a hidden/deactivated identity.
    result = []
    for p in rows[:PAGE_SIZE]:
        user = db.get(User, p.student_id)
        name = p.public_name if p.enabled and not p.name_change_required and user and user.is_active else 'Unavailable learner'
        result.append({'ref':p.public_ref, 'publicName':name, 'avatar':None, 'subjects':[], 'following':False, 'followsYou':False})
    return {'members':result, 'page':page, 'hasMore':len(rows)>PAGE_SIZE}


def feed_query(actor):
    return select(Notice).where(Notice.recipient_id == actor,
        Notice.actor_id.in_(visible_query(actor).with_only_columns(Profile.student_id)))


def feed(db, actor, page):
    p = own(db, actor)
    if not p or not p.enabled or p.name_change_required:
        return {'notifications':[], 'unreadCount':0, 'hasMore':False, 'page':page}
    query = feed_query(actor)
    unread = db.scalar(select(func.count()).select_from(query.where(Notice.read.is_(False)).subquery()))
    rows = list(db.scalars(query.order_by(Notice.created_at.desc(), Notice.id).offset((page-1)*PAGE_SIZE).limit(PAGE_SIZE+1)))
    return {'notifications':[{'ref':n.public_ref,'type':n.event_type,'actor':member(db, actor, db.get(Profile,n.actor_id)), 'createdAt':n.created_at,'read':n.read} for n in rows[:PAGE_SIZE]], 'unreadCount':unread, 'hasMore':len(rows)>PAGE_SIZE, 'page':page}


def read_notice(db, actor, ref, read):
    own(db, actor, participating=True)
    n = db.scalar(feed_query(actor).where(Notice.public_ref == ref))
    if n is None: raise HTTPException(404, 'Notification is unavailable.')
    n.read = read
    db.commit()
    return {'ok':True}


def report(db, actor, ref, reason):
    p = target(db, actor, ref)
    lock(db, actor, p.student_id)
    me = own(db, actor, participating=True)
    target(db, actor, ref)
    throttle(me)
    existing = db.scalar(select(Report).where(Report.reporter_id==actor, Report.target_id==p.student_id))
    if existing is None:
        db.add(Report(reporter_id=actor, target_id=p.student_id, reason=reason, reported_name=p.public_name))
    elif existing.status != 'open' and utc(existing.updated_at) < now()-timedelta(hours=24):
        existing.status, existing.reason, existing.reviewed_by, existing.reported_name = 'open', reason, None, p.public_name
    audit(db, actor, 'community.report', ref)
    db.commit()
    return {'ok':True}


def reports(db, status, page):
    rows = list(db.scalars(select(Report).where(Report.status==status).order_by(Report.created_at.desc(),Report.id).offset((page-1)*PAGE_SIZE).limit(PAGE_SIZE+1)))
    return {'reports':[{'ref':r.public_ref,'publicName':r.reported_name, 'reason':r.reason,'status':r.status,'createdAt':r.created_at} for r in rows[:PAGE_SIZE]], 'hasMore':len(rows)>PAGE_SIZE,'page':page}


def review_report(db, actor, ref, action):
    r = db.scalar(select(Report).where(Report.public_ref==ref))
    if r is None: raise HTTPException(404, 'Report is unavailable.')
    lock(db, r.target_id)
    if r.status != 'open': raise HTTPException(409, 'This report has already been reviewed.')
    if action == 'name_change_required':
        p = db.get(Profile,r.target_id)
        if p.public_name != r.reported_name:
            raise HTTPException(409, 'This public name has changed since the report. Dismiss the old report or review a newer one.')
        p.enabled, p.name_change_required = False, True
    r.status, r.reviewed_by = action, actor
    audit(db, actor, 'community.report.'+action, ref)
    db.commit()
    return {'ok':True}
