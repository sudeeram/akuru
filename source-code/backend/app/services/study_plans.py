import hashlib, uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.errors import DomainError
from app.models import (AssessmentBlueprint, Document, ImprovementRecommendation, RetrievalChunk, StudentProfile,
    StudentProgression, StudentSubject, StudyPlan, StudyPlanItem, TextbookUnit, UnitMastery, WeaknessDiagnosis)
from app.schemas.study_plans import PlanHistoryResponse, PlanItemResponse, StudyPlanResponse
from app.services.curriculum_plans import student_coverage

def _now(): return datetime.now(timezone.utc)

def authorize(db, principal, student_id):
    profile = db.get(StudentProfile, student_id)
    if not profile: raise DomainError("student_not_found", "Student not found.", 404)
    if principal.user.role == "student" and principal.user.id != student_id: raise DomainError("student_access_denied", "Students may only use their own study plan.", 403)
    if principal.user.role == "parent" and profile.parent_id != principal.user.id: raise DomainError("student_access_denied", "This student is not linked to your parent account.", 403)

def _eligible_rows(db, student_id):
    subjects = set(db.scalars(select(StudentSubject.subject_id).where(StudentSubject.student_id == student_id)).all())
    covered = set()
    for subject in subjects:
        scope = student_coverage(db, student_id, subject)
        if scope.status == "ready": covered |= {uuid.UUID(row.id) for row in scope.coveredUnits}
    rows = db.execute(select(ImprovementRecommendation, WeaknessDiagnosis, UnitMastery).join(
        WeaknessDiagnosis, WeaknessDiagnosis.id == ImprovementRecommendation.diagnosis_id).outerjoin(
        UnitMastery, (UnitMastery.student_id == ImprovementRecommendation.student_id) &
        (UnitMastery.unit_id == ImprovementRecommendation.unit_id)).where(
        ImprovementRecommendation.student_id == student_id, ImprovementRecommendation.review_status == "approved",
        ImprovementRecommendation.subject_id.in_(subjects), ImprovementRecommendation.unit_id.in_(covered))).all()
    return rows

def _fingerprint(rows):
    value = "|".join(sorted(f"{r.id}:{d.occurrence_number}:{m.version_number if m else 0}:{r.review_status}" for r,d,m in rows))
    return hashlib.sha256(value.encode()).hexdigest()

def _priority(row, upcoming):
    recommendation, diagnosis, mastery = row
    score = (10 - float(mastery.score)) if mastery else 5
    score += 2 if mastery and mastery.trend < 0 else 0
    score += 1.5 if not mastery or mastery.confidence == "low" else 0
    score += min(2, diagnosis.occurrence_number - 1)
    score += 1 if recommendation.subject_id in upcoming else 0
    return score

def _balanced(rows, upcoming, limit=8):
    by_subject = defaultdict(list)
    for row in rows: by_subject[row[0].subject_id].append(row)
    for subject in by_subject: by_subject[subject].sort(key=lambda row: (-_priority(row, upcoming), row[0].created_at))
    queues = deque(sorted(by_subject, key=lambda subject: (-max(_priority(row, upcoming) for row in by_subject[subject]), subject)))
    selected=[]
    while queues and len(selected) < limit:
        subject=queues.popleft(); selected.append(by_subject[subject].pop(0))
        if by_subject[subject]: queues.append(subject)
    return selected

def generate(db, student_id, requested_by=None, force=False):
    db.scalar(select(StudentProfile).where(StudentProfile.student_id == student_id).with_for_update())
    rows = _eligible_rows(db, student_id); fingerprint = _fingerprint(rows)
    current = db.scalar(select(StudyPlan).where(StudyPlan.student_id == student_id, StudyPlan.status == "active"))
    if current and current.evidence_fingerprint == fingerprint and not force: return response(db, current)
    progression = db.scalar(select(StudentProgression).where(StudentProgression.student_id == student_id, StudentProgression.is_current.is_(True)))
    upcoming = set(db.scalars(select(AssessmentBlueprint.subject_id).where(AssessmentBlueprint.status == "published",
        AssessmentBlueprint.grade == (progression.grade if progression else -1),
        AssessmentBlueprint.term == (progression.term if progression else -1))).all())
    if current: current.status="superseded"; current.superseded_at=_now()
    version=(db.scalar(select(func.max(StudyPlan.version_number)).where(StudyPlan.student_id == student_id)) or 0)+1
    plan=StudyPlan(student_id=student_id, version_number=version, status="active", evidence_fingerprint=fingerprint,
        generation_reason="request" if force else "evidence", requested_by=requested_by)
    db.add(plan); db.flush()
    durations={"review":15,"targeted_practice":20,"spaced_retry":15,"unit_check":20}
    for index,(recommendation,diagnosis,mastery) in enumerate(_balanced(rows, upcoming),1):
        reason=recommendation.reason
        if mastery and mastery.trend < 0: reason += " Recent mastery is declining."
        if mastery and mastery.confidence == "low": reason += " More evidence is needed to improve confidence."
        if recommendation.subject_id in upcoming: reason += " This subject has a current-term assessment blueprint."
        scheduled=_now()+timedelta(days=3 if recommendation.activity_type == "spaced_retry" else max(0,index-1))
        db.add(StudyPlanItem(plan_id=plan.id,student_id=student_id,recommendation_id=recommendation.id,
            subject_id=recommendation.subject_id,unit_id=recommendation.unit_id,sequence=index,
            activity_type=recommendation.activity_type,title=recommendation.title,duration_minutes=durations[recommendation.activity_type],
            reason=reason,source_chunk_id=recommendation.source_chunk_id,success_condition=recommendation.success_condition,
            scheduled_for=scheduled,status="planned"))
    db.commit(); return response(db, plan)

def response(db, plan):
    rows=db.execute(select(StudyPlanItem,TextbookUnit,RetrievalChunk,Document).join(TextbookUnit,TextbookUnit.id==StudyPlanItem.unit_id).join(
        RetrievalChunk,RetrievalChunk.id==StudyPlanItem.source_chunk_id).join(Document,Document.id==RetrievalChunk.document_id).where(
        StudyPlanItem.plan_id==plan.id).order_by(StudyPlanItem.sequence)).all()
    return StudyPlanResponse(id=plan.id,studentId=plan.student_id,version=plan.version_number,updatedAt=plan.created_at,
        generationReason=plan.generation_reason,items=[PlanItemResponse(id=i.id,subject=i.subject_id,unitId=i.unit_id,
        unitCode=u.unit_code,topic=i.title,activityType=i.activity_type,minutes=i.duration_minutes,reason=i.reason,
        source=f"{d.title} · page {c.page_number}",sourceUrl=f"/api/v1/retrieval/evidence/{c.id}?studentId={i.student_id}",
        successCondition=i.success_condition,scheduledFor=i.scheduled_for,status=i.status) for i,u,c,d in rows])

def current(db, principal, student_id):
    authorize(db,principal,student_id)
    return generate(db,student_id)

def history(db, principal, student_id):
    authorize(db,principal,student_id)
    return PlanHistoryResponse(plans=[response(db,row) for row in db.scalars(select(StudyPlan).where(
        StudyPlan.student_id==student_id).order_by(StudyPlan.version_number.desc())).all()])

def complete(db, principal, item_id):
    item=db.get(StudyPlanItem,item_id)
    if not item: raise DomainError("study_plan_item_not_found","Study plan item not found.",404)
    authorize(db,principal,item.student_id)
    if principal.user.role != "student": raise DomainError("study_plan_completion_denied","Only the student can complete a study plan item.",403)
    item.status="completed"; item.completed_at=_now(); db.commit()
    return response(db,db.get(StudyPlan,item.plan_id))
