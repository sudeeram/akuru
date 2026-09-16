import uuid
from datetime import datetime, timezone
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from app.errors import DomainError
from app.models import (AssessmentCurriculumSnapshot, AuditEvent, CurriculumPlan, CurriculumPlanTopic,
    CurriculumPlanUnit, Document, OfficialMaterialVersion, OfficialQuestionTopicMapping, OfficialQuestionUnitMapping, OfficialQuestionVersion,
    StudentProgression, StudentSubject, Textbook, TextbookContentVersion, TextbookGroup, TextbookTopic,
    TextbookTopicContentVersion, TextbookUnit)
from app.schemas.curriculum_plans import (CoverageDiagnosticResponse, CurriculumPlanResponse, PlanChangeResponse,
    PlanPeriod, PlanTopicGroupResponse, PlanTopicResponse, PlanUnitResponse, QuestionPoolDiagnosticResponse, SavePlanRequest)
from app.security import Principal

PERIODS = tuple((g, t) for g in (10, 11) for t in (1, 2, 3))

def _book(db, subject):
    return db.scalar(select(Textbook).where(Textbook.course_id == "igcse", Textbook.subject_id == subject,
        Textbook.status == "published").order_by(Textbook.published_at.desc()))

def _legacy_book(db, subject):
    row = db.execute(select(TextbookContentVersion, Document).join(Document).where(
        TextbookContentVersion.course_id == "igcse", TextbookContentVersion.subject_id == subject,
        TextbookContentVersion.status == "published", Document.removed_at.is_(None)
    ).order_by(TextbookContentVersion.published_at.desc())).first()
    if not row: raise DomainError("published_textbook_required", "Publish a textbook for this subject first.", 409)
    return row

def _plan(db, subject, status=("draft", "published")):
    return db.scalar(select(CurriculumPlan).where(CurriculumPlan.course_id == "igcse",
        CurriculumPlan.subject_id == subject, CurriculumPlan.status.in_(status)).order_by(CurriculumPlan.version_number.desc()))

def _units(db, content_id):
    return db.scalars(select(TextbookUnit).where(TextbookUnit.content_version_id == content_id).order_by(TextbookUnit.sequence)).all() if content_id else []

def _topics(db, book):
    published = select(TextbookTopicContentVersion.topic_id).where(TextbookTopicContentVersion.status == "published")
    return db.scalars(select(TextbookTopic).join(TextbookGroup, TextbookGroup.id == TextbookTopic.group_id).where(
        TextbookTopic.textbook_id == book.id, TextbookTopic.status == "published", TextbookTopic.id.in_(published)
    ).order_by(TextbookGroup.sequence, TextbookTopic.sequence)).all()

def _assignments(db, plan):
    if not plan: return {}
    return {r.topic_id: (r.grade, r.term) for r in db.scalars(select(CurriculumPlanTopic).where(CurriculumPlanTopic.plan_id == plan.id)).all()}

def _topic_out(topic, group):
    return PlanTopicResponse(topicRef=topic.public_ref, code=topic.code, title=topic.title,
        groupRef=group.public_ref, groupCode=group.code, groupTitle=group.title)

def _periods(db, plan, topics):
    assigned, refs = _assignments(db, plan), {t.id: t.public_ref for t in topics}
    return [PlanPeriod(grade=g, term=t, topicRefs=[refs[i] for i, p in assigned.items() if p == (g, t) and i in refs]) for g, t in PERIODS]

def _changes(db, plan, topics):
    if not plan or not plan.based_on_plan_id: return []
    old, new, by_id = _assignments(db, db.get(CurriculumPlan, plan.based_on_plan_id)), _assignments(db, plan), {t.id: t for t in topics}
    result = []
    for ident in set(old) | set(new):
        topic = by_id.get(ident)
        if not topic: continue
        label = lambda p: f"Grade {p[0]} Term {p[1]}"
        if ident not in old: result.append(PlanChangeResponse(topicRef=topic.public_ref, code=topic.code, title=topic.title, change="added", toPeriod=label(new[ident])))
        elif ident not in new: result.append(PlanChangeResponse(topicRef=topic.public_ref, code=topic.code, title=topic.title, change="removed", fromPeriod=label(old[ident])))
        elif old[ident] != new[ident]: result.append(PlanChangeResponse(topicRef=topic.public_ref, code=topic.code, title=topic.title, change="moved", fromPeriod=label(old[ident]), toPeriod=label(new[ident])))
    return sorted(result, key=lambda r: (r.code, r.change))

def _topic_response(db, plan, book):
    topics = _topics(db, book)
    groups = db.scalars(select(TextbookGroup).where(TextbookGroup.textbook_id == book.id, TextbookGroup.status == "published").order_by(TextbookGroup.sequence)).all()
    published = db.get(CurriculumPlan, plan.based_on_plan_id) if plan and plan.based_on_plan_id else (plan if plan and plan.status == "published" else None)
    changes = _changes(db, plan, topics)
    return CurriculumPlanResponse(versionNumber=plan.version_number if plan else 0, status=plan.status if plan else "not_started",
        subjectId=book.subject_id, textbookTitle=book.title, textbookEdition=book.edition, availableUnits=[], groupLabel=book.group_label,
        groups=[PlanTopicGroupResponse(groupRef=g.public_ref, code=g.code, title=g.title,
            topics=[_topic_out(t, g) for t in topics if t.group_id == g.id]) for g in groups],
        periods=_periods(db, plan, topics), publishedPeriods=_periods(db, published, topics), changes=changes,
        requiresPublishedChangeConfirmation=any(c.change in ("removed", "moved") for c in changes),
        basedOnVersion=published.version_number if published else None,
        createdAt=plan.created_at.isoformat() if plan and plan.created_at else None,
        publishedAt=plan.published_at.isoformat() if plan and plan.published_at else None)

def _legacy_response(db, plan, document):
    units, rows = _units(db, plan.textbook_content_version_id), db.scalars(select(CurriculumPlanUnit).where(CurriculumPlanUnit.plan_id == plan.id)).all()
    return CurriculumPlanResponse(versionNumber=plan.version_number, status=plan.status, subjectId=plan.subject_id,
        textbookTitle=document.title, textbookEdition=document.edition or "", availableUnits=[PlanUnitResponse(id=str(u.id), code=u.unit_code, title=u.title) for u in units],
        periods=[PlanPeriod(grade=g, term=t, unitIds=[str(r.unit_id) for r in rows if (r.grade, r.term) == (g, t)]) for g, t in PERIODS])

def get_plan(db: Session, subject_id: str):
    book = _book(db, subject_id)
    if book: return _topic_response(db, _plan(db, subject_id), book)
    content, document = _legacy_book(db, subject_id); plan = _plan(db, subject_id)
    if plan: return _legacy_response(db, plan, document)
    return CurriculumPlanResponse(versionNumber=0, status="not_started", subjectId=subject_id, textbookTitle=document.title,
        textbookEdition=document.edition or "", availableUnits=[PlanUnitResponse(id=str(u.id), code=u.unit_code, title=u.title) for u in _units(db, content.id)],
        periods=[PlanPeriod(grade=g, term=t) for g, t in PERIODS])

def create_next_draft(db: Session, principal: Principal, subject_id: str):
    book = _book(db, subject_id)
    if not book: raise DomainError("topic_textbook_required", "Publish the logical textbook structure before creating topic coverage.", 409)
    current = _plan(db, subject_id)
    if current and current.status == "draft": return _topic_response(db, current, book)
    base = _plan(db, subject_id, ("published",)); number = (db.scalar(select(func.max(CurriculumPlan.version_number)).where(CurriculumPlan.course_id == "igcse", CurriculumPlan.subject_id == subject_id)) or 0) + 1
    plan = CurriculumPlan(course_id="igcse", subject_id=subject_id, textbook_id=book.id, textbook_content_version_id=None,
        based_on_plan_id=base.id if base else None, version_number=number, status="draft", created_by=principal.user.id)
    db.add(plan); db.flush()
    for row in db.scalars(select(CurriculumPlanTopic).where(CurriculumPlanTopic.plan_id == base.id)).all() if base else []:
        db.add(CurriculumPlanTopic(plan_id=plan.id, grade=row.grade, term=row.term, topic_id=row.topic_id))
    db.add(AuditEvent(actor_id=principal.user.id, action="curriculum_plan.draft_created", target_type="curriculum_plan", target_id=str(plan.id), event_data={"subjectId": subject_id, "versionNumber": number, "basedOnVersion": base.version_number if base else None}))
    db.commit(); db.refresh(plan); return _topic_response(db, plan, book)

def save_plan(db: Session, principal: Principal, subject_id: str, payload: SavePlanRequest):
    book = _book(db, subject_id)
    if book:
        plan = _plan(db, subject_id)
        if not plan or plan.status != "draft": create_next_draft(db, principal, subject_id); plan = _plan(db, subject_id)
        if plan.textbook_id != book.id: raise DomainError("curriculum_textbook_superseded", "Create a draft using the active textbook edition.", 409)
        if len({(p.grade, p.term) for p in payload.periods}) != len(payload.periods): raise DomainError("duplicate_curriculum_period", "Each Grade and Term may appear only once.", 409)
        allowed = {t.public_ref: t for t in _topics(db, book)}; selected = [ref for p in payload.periods for ref in p.topicRefs]
        if any(ref not in allowed for ref in selected): raise DomainError("invalid_curriculum_topic", "Coverage may use only published topics from the active subject textbook.", 422)
        if len(selected) != len(set(selected)): raise DomainError("duplicate_curriculum_topic", "A topic may be introduced in only one Grade and Term.", 409)
        db.execute(delete(CurriculumPlanTopic).where(CurriculumPlanTopic.plan_id == plan.id))
        for p in payload.periods:
            for ref in p.topicRefs: db.add(CurriculumPlanTopic(plan_id=plan.id, grade=p.grade, term=p.term, topic_id=allowed[ref].id))
        db.add(AuditEvent(actor_id=principal.user.id, action="curriculum_plan.saved", target_type="curriculum_plan", target_id=str(plan.id), event_data={"subjectId": subject_id, "versionNumber": plan.version_number, "topicCount": len(selected)}))
        db.commit(); db.refresh(plan); return _topic_response(db, plan, book)
    content, document = _legacy_book(db, subject_id); plan = _plan(db, subject_id)
    if plan and plan.status == "published": plan = None
    if not plan:
        number = (db.scalar(select(func.max(CurriculumPlan.version_number)).where(CurriculumPlan.subject_id == subject_id)) or 0) + 1
        plan = CurriculumPlan(course_id="igcse", subject_id=subject_id, textbook_content_version_id=content.id, version_number=number, status="draft", created_by=principal.user.id); db.add(plan); db.flush()
    allowed = {str(u.id) for u in _units(db, content.id)}; selected = [x for p in payload.periods for x in p.unitIds]
    if any(x not in allowed for x in selected): raise DomainError("invalid_curriculum_unit", "Coverage may use only units from this published subject textbook.", 422)
    if len(selected) != len(set(selected)): raise DomainError("duplicate_curriculum_unit", "A unit may be introduced in only one Grade and Term.", 409)
    db.execute(delete(CurriculumPlanUnit).where(CurriculumPlanUnit.plan_id == plan.id))
    for p in payload.periods:
        for ident in p.unitIds: db.add(CurriculumPlanUnit(plan_id=plan.id, grade=p.grade, term=p.term, unit_id=uuid.UUID(ident)))
    db.commit(); db.refresh(plan); return _legacy_response(db, plan, document)

def publish_plan(db: Session, principal: Principal, subject_id: str, confirmation):
    plan = _plan(db, subject_id)
    if not plan or plan.status != "draft": raise DomainError("curriculum_draft_required", "Create and save a curriculum-plan draft first.", 409)
    if not confirmation.confirmSubject or not confirmation.confirmTextbook: raise DomainError("curriculum_confirmation_required", "Confirm subject and textbook before publishing.", 422)
    book = _book(db, subject_id)
    if book:
        response = _topic_response(db, plan, book)
        if plan.textbook_id != book.id: raise DomainError("curriculum_textbook_superseded", "Create a draft using the active textbook edition.", 409)
        if not _assignments(db, plan): raise DomainError("curriculum_topics_required", "Assign at least one published topic before publishing.", 409)
        if response.requiresPublishedChangeConfirmation and not confirmation.confirmPublishedChanges: raise DomainError("curriculum_published_change_confirmation_required", "Confirm the impact before removing or moving previously published topic coverage.", 409, [c.model_dump() for c in response.changes if c.change != "added"])
    else:
        content, document = _legacy_book(db, subject_id)
        if plan.textbook_content_version_id != content.id: raise DomainError("curriculum_textbook_superseded", "Rebuild the plan using the currently published textbook.", 409)
        if not db.scalar(select(func.count()).select_from(CurriculumPlanUnit).where(CurriculumPlanUnit.plan_id == plan.id)): raise DomainError("curriculum_units_required", "Assign at least one unit before publishing.", 409)
    now = datetime.now(timezone.utc)
    for old in db.scalars(select(CurriculumPlan).where(CurriculumPlan.course_id == "igcse", CurriculumPlan.subject_id == subject_id, CurriculumPlan.status == "published").with_for_update()).all(): old.status, old.superseded_at = "superseded", now
    plan.status, plan.published_by, plan.published_at = "published", principal.user.id, now
    db.add(AuditEvent(actor_id=principal.user.id, action="curriculum_plan.published", target_type="curriculum_plan", target_id=str(plan.id), event_data={"subjectId": subject_id, "versionNumber": plan.version_number}))
    db.commit(); db.refresh(plan); return _topic_response(db, plan, book) if book else _legacy_response(db, plan, document)

def student_coverage(db: Session, student_id: uuid.UUID, subject_id: str):
    if not db.get(StudentSubject, {"student_id": student_id, "subject_id": subject_id}): raise DomainError("student_subject_not_enrolled", "The student is not enrolled in this subject.", 409)
    progress = db.scalars(select(StudentProgression).where(StudentProgression.student_id == student_id, StudentProgression.course_id == "igcse").order_by(StudentProgression.grade, StudentProgression.term)).all(); current = next((r for r in progress if r.is_current), None)
    if not current: return CoverageDiagnosticResponse(status="missing_progression", message="Configure the student's current Grade and Term.")
    plan = _plan(db, subject_id, ("published",))
    if not plan: return CoverageDiagnosticResponse(status="missing_plan", message="Publish curriculum coverage for this subject.", currentGrade=current.grade, currentTerm=current.term)
    reached = {(r.grade, r.term) for r in progress if (r.grade, r.term) <= (current.grade, current.term)}
    if plan.textbook_id:
        rows = db.scalars(select(CurriculumPlanTopic).where(CurriculumPlanTopic.plan_id == plan.id)).all(); missing = [f"Grade {g} Term {t}" for g, t in sorted(reached) if not any((r.grade, r.term) == (g, t) for r in rows)]
        if missing: return CoverageDiagnosticResponse(status="missing_coverage", message="Topic coverage is missing for part of the student's progression.", planVersion=plan.version_number, currentGrade=current.grade, currentTerm=current.term, missingPeriods=missing)
        topics = db.scalars(select(TextbookTopic).where(TextbookTopic.id.in_({r.topic_id for r in rows if (r.grade, r.term) in reached})).order_by(TextbookTopic.sequence)).all(); groups = {g.id:g for g in db.scalars(select(TextbookGroup).where(TextbookGroup.textbook_id == plan.textbook_id)).all()}
        return CoverageDiagnosticResponse(status="ready", message="Cumulative topic coverage is ready.", planVersion=plan.version_number, currentGrade=current.grade, currentTerm=current.term, coveredTopics=[_topic_out(t, groups[t.group_id]) for t in topics])
    rows = db.scalars(select(CurriculumPlanUnit).where(CurriculumPlanUnit.plan_id == plan.id)).all(); missing = [f"Grade {g} Term {t}" for g,t in sorted(reached) if not any((r.grade,r.term)==(g,t) for r in rows)]
    if missing: return CoverageDiagnosticResponse(status="missing_coverage", message="Coverage is missing for part of the student's progression.", planVersion=plan.version_number, currentGrade=current.grade, currentTerm=current.term, missingPeriods=missing)
    units = db.scalars(select(TextbookUnit).where(TextbookUnit.id.in_({r.unit_id for r in rows if (r.grade,r.term) in reached})).order_by(TextbookUnit.sequence)).all()
    return CoverageDiagnosticResponse(status="ready", message="Cumulative coverage is ready.", planVersion=plan.version_number, currentGrade=current.grade, currentTerm=current.term, coveredUnits=[PlanUnitResponse(id=str(u.id), code=u.unit_code, title=u.title) for u in units])

def snapshot(db: Session, assessment_ref: str, student_id: uuid.UUID, subject_id: str):
    existing = db.scalar(select(AssessmentCurriculumSnapshot).where(AssessmentCurriculumSnapshot.assessment_ref == assessment_ref))
    if existing: return existing
    coverage = student_coverage(db, student_id, subject_id)
    if coverage.status != "ready": raise DomainError("assessment_coverage_not_ready", coverage.message, 409, [{"missingPeriods": coverage.missingPeriods}])
    plan = _plan(db, subject_id, ("published",)); progress = db.scalars(select(StudentProgression).where(StudentProgression.student_id == student_id).order_by(StudentProgression.grade, StudentProgression.term)).all(); current = next(r for r in progress if r.is_current)
    topic_ids = [str(x) for x in db.scalars(select(TextbookTopic.id).where(TextbookTopic.public_ref.in_([t.topicRef for t in coverage.coveredTopics]))).all()] if coverage.coveredTopics else []
    row = AssessmentCurriculumSnapshot(assessment_ref=assessment_ref, student_id=student_id, plan_id=plan.id, course_id="igcse", subject_id=subject_id, grade=current.grade, term=current.term, covered_unit_ids=[u.id for u in coverage.coveredUnits], covered_topic_ids=topic_ids, progression_periods=[{"grade":r.grade,"term":r.term} for r in progress if (r.grade,r.term)<=(current.grade,current.term)])
    db.add(row); db.commit(); db.refresh(row); return row

def question_pool_diagnostic(db: Session, student_id: uuid.UUID, subject_id: str, requested_question_count: int=0, requested_marks: int=0):
    coverage = student_coverage(db, student_id, subject_id)
    if coverage.status != "ready": return QuestionPoolDiagnosticResponse(status=coverage.status, message=coverage.message, planVersion=coverage.planVersion, requestedQuestionCount=requested_question_count, requestedMarks=requested_marks, shortageQuestionCount=requested_question_count, shortageMarks=requested_marks)
    if coverage.coveredTopics:
        covered_refs={row.topicRef for row in coverage.coveredTopics}; covered=set(db.scalars(select(TextbookTopic.id).where(TextbookTopic.public_ref.in_(covered_refs))).all())
        questions=db.scalars(select(OfficialQuestionVersion).join(OfficialMaterialVersion).where(OfficialMaterialVersion.course_id=="igcse",OfficialMaterialVersion.subject_id==subject_id,OfficialMaterialVersion.kind=="past_paper",OfficialMaterialVersion.status=="published",OfficialQuestionVersion.mapping_status=="confirmed")).all(); eligible=[]; missing=set()
        for question in questions:
            rows=db.scalars(select(OfficialQuestionTopicMapping).where(OfficialQuestionTopicMapping.question_version_id==question.id,OfficialQuestionTopicMapping.status=="confirmed")).all(); required={row.topic_id for row in rows if row.required}
            if required and required.issubset(covered): eligible.append(question)
            else: missing.update(required-covered)
        count,marks=len(eligible),sum(q.marks for q in eligible); sc,sm=max(0,requested_question_count-count),max(0,requested_marks-marks); ready=sc==0 and sm==0
        missing_topics=db.scalars(select(TextbookTopic).where(TextbookTopic.id.in_(missing)).order_by(TextbookTopic.sequence)).all() if missing else []
        reason=(" Missing required topics: "+", ".join(f"{t.code} · {t.title}" for t in missing_topics)+".") if missing_topics else ""
        return QuestionPoolDiagnosticResponse(status="ready" if ready else "question_pool_shortage",message=("The eligible topic-mapped question pool is ready." if ready else "The eligible topic-mapped question pool is too small."+reason),planVersion=coverage.planVersion,eligibleQuestionCount=count,eligibleMarks=marks,requestedQuestionCount=requested_question_count,requestedMarks=requested_marks,shortageQuestionCount=sc,shortageMarks=sm)
    covered={uuid.UUID(u.id) for u in coverage.coveredUnits}; questions=db.scalars(select(OfficialQuestionVersion).join(OfficialMaterialVersion).where(OfficialMaterialVersion.course_id=="igcse",OfficialMaterialVersion.subject_id==subject_id,OfficialMaterialVersion.kind=="past_paper",OfficialMaterialVersion.status=="published",OfficialQuestionVersion.mapping_status=="confirmed")).all(); eligible=[]
    for q in questions:
        mappings=set(db.scalars(select(OfficialQuestionUnitMapping.unit_id).where(OfficialQuestionUnitMapping.question_version_id==q.id,OfficialQuestionUnitMapping.status=="confirmed")).all())
        if mappings and mappings.issubset(covered): eligible.append(q)
    count,marks=len(eligible),sum(q.marks for q in eligible); sc,sm=max(0,requested_question_count-count),max(0,requested_marks-marks); ready=sc==0 and sm==0
    return QuestionPoolDiagnosticResponse(status="ready" if ready else "question_pool_shortage",message="The eligible question pool is ready." if ready else "The eligible question pool is too small for this assessment.",planVersion=coverage.planVersion,eligibleQuestionCount=count,eligibleMarks=marks,requestedQuestionCount=requested_question_count,requestedMarks=requested_marks,shortageQuestionCount=sc,shortageMarks=sm)
