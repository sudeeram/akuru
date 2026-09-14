import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import (Assessment, AssessmentAnswer, AssessmentBlueprint, AssessmentInteraction, AssessmentQuestion, AssessmentWorkingFile,
    Document, ExaminerCommentVersion, MarkSchemeEntryVersion, OfficialMaterialVersion,
    OfficialQuestionUnitMapping, OfficialQuestionVersion, StudentProgression, StudentSubject)
from app.schemas.assessments import AssessmentListResponse, AssessmentQuestionResponse, AssessmentResponse, BlueprintCreate, BlueprintResponse
from app.security import Principal
from app.services.curriculum_plans import snapshot, student_coverage
from app.services import assessment_marking

def _now(): return datetime.now(timezone.utc)

def blueprint_response(row):
    return BlueprintResponse(id=row.id, name=row.name, subjectId=row.subject_id, grade=row.grade, term=row.term,
        mode=row.mode, targetMarks=row.target_marks, durationMinutes=row.duration_minutes,
        questionCount=row.question_count, skills=row.skills, difficultyProfile=row.difficulty_profile, status=row.status)

def create_blueprint(db: Session, principal: Principal, payload: BlueprintCreate):
    row = AssessmentBlueprint(name=payload.name, course_id="igcse", subject_id=payload.subjectId,
        grade=payload.grade, term=payload.term, mode=payload.mode, target_marks=payload.targetMarks,
        duration_minutes=payload.durationMinutes, question_count=payload.questionCount, skills=payload.skills,
        difficulty_profile=payload.difficultyProfile, status="published", created_by=principal.user.id, published_at=_now())
    db.add(row); db.commit(); db.refresh(row); return blueprint_response(row)

def list_blueprints(db: Session, principal: Principal):
    query = select(AssessmentBlueprint).where(AssessmentBlueprint.status == "published")
    if principal.user.role == "student":
        progress = db.scalar(select(StudentProgression).where(StudentProgression.student_id == principal.user.id, StudentProgression.is_current.is_(True)))
        if not progress: return []
        query = query.where(AssessmentBlueprint.grade == progress.grade, AssessmentBlueprint.term == progress.term)
    return [blueprint_response(row) for row in db.scalars(query.order_by(AssessmentBlueprint.subject_id, AssessmentBlueprint.name)).all()]

def official_papers(db: Session, student_id: uuid.UUID):
    subject_ids = list(db.scalars(select(StudentSubject.subject_id).where(StudentSubject.student_id == student_id)).all())
    result = []
    for subject_id in subject_ids:
        try: eligible = eligible_questions(db, student_id, subject_id)
        except DomainError: continue
        by_paper = {}
        for row in eligible: by_paper.setdefault(row[1].id, []).append(row)
        for paper_id, rows in by_paper.items():
            total = db.scalar(select(func.count()).select_from(OfficialQuestionVersion).where(
                OfficialQuestionVersion.material_version_id == paper_id))
            if total == len(rows):
                material = rows[0][1]; document = db.get(Document, material.document_id)
                result.append({"id": str(document.id), "subjectId": subject_id, "title": document.title,
                    "questionCount": total, "marks": sum(row[0].marks for row in rows)})
    return result

def eligible_questions(db: Session, student_id: uuid.UUID, subject_id: str):
    coverage = student_coverage(db, student_id, subject_id)
    if coverage.status != "ready": raise DomainError("assessment_coverage_not_ready", coverage.message, 409)
    allowed = {uuid.UUID(unit.id) for unit in coverage.coveredUnits}
    questions = db.execute(select(OfficialQuestionVersion, OfficialMaterialVersion).join(
        OfficialMaterialVersion, OfficialMaterialVersion.id == OfficialQuestionVersion.material_version_id).where(
        OfficialMaterialVersion.course_id == "igcse", OfficialMaterialVersion.subject_id == subject_id,
        OfficialMaterialVersion.kind == "past_paper", OfficialMaterialVersion.status == "published",
        OfficialQuestionVersion.mapping_status == "confirmed")).all()
    result = []
    for question, material in questions:
        units = list(db.scalars(select(OfficialQuestionUnitMapping.unit_id).where(
            OfficialQuestionUnitMapping.question_version_id == question.id, OfficialQuestionUnitMapping.status == "confirmed")).all())
        if units and set(units).issubset(allowed): result.append((question, material, units))
    return result

def _choose(candidates, count, marks, seed):
    ordered = sorted(candidates, key=lambda row: hashlib.sha256(f"{seed}:{row[0].id}".encode()).hexdigest())
    if count == 1 and marks == 0: return ordered[:1]
    def visit(start, chosen, total):
        if len(chosen) == count: return chosen if total == marks else None
        for index in range(start, len(ordered)):
            total2 = total + ordered[index][0].marks
            if total2 <= marks:
                found = visit(index + 1, chosen + [ordered[index]], total2)
                if found: return found
        return None
    return visit(0, [], 0) or []

def _rubric(db, paper_version_id, number):
    scheme = db.scalar(select(OfficialMaterialVersion).where(OfficialMaterialVersion.kind == "mark_scheme",
        OfficialMaterialVersion.source_paper_version_id == paper_version_id, OfficialMaterialVersion.status == "published"))
    report = db.scalar(select(OfficialMaterialVersion).where(OfficialMaterialVersion.kind == "examiner_report",
        OfficialMaterialVersion.source_paper_version_id == paper_version_id, OfficialMaterialVersion.status == "published"))
    entry = db.scalar(select(MarkSchemeEntryVersion).where(MarkSchemeEntryVersion.material_version_id == scheme.id,
        MarkSchemeEntryVersion.question_number == number)) if scheme else None
    comment = db.scalar(select(ExaminerCommentVersion).where(ExaminerCommentVersion.material_version_id == report.id,
        ExaminerCommentVersion.question_number == number)) if report else None
    return {"rubricVersion": str(entry.material_version_id) if entry else None,
        "examinerReportVersion": str(comment.material_version_id) if comment else None,
        "markingPoints": entry.marking_points if entry else [], "alternatives": entry.alternatives if entry else [],
        "commonMistakes": comment.common_mistakes if comment else [], "examinerAdvice": comment.advice if comment else []}

def _unit_weights(db, question_id, units):
    rows = db.execute(select(OfficialQuestionUnitMapping.unit_id, OfficialQuestionUnitMapping.weight).where(
        OfficialQuestionUnitMapping.question_version_id == question_id,
        OfficialQuestionUnitMapping.status == "confirmed")).all()
    weights = {str(unit_id): weight for unit_id, weight in rows if unit_id in units}
    if weights and sum(weights.values()) == 100: return weights
    base, remainder = divmod(100, len(units))
    return {str(unit_id): base + (1 if index < remainder else 0) for index, unit_id in enumerate(units)}

def start(db, principal, payload):
    student_id = principal.user.id
    active = db.scalar(select(Assessment).where(Assessment.student_id == student_id, Assessment.status == "active"))
    if active and active.ends_at > _now(): raise DomainError("assessment_already_active", "Finish the active assessment before starting another.", 409)
    if active:
        active.status = "expired"
        db.commit()
    candidates = eligible_questions(db, student_id, payload.subjectId); blueprint = None; paper_version = None
    if payload.mode == "mock":
        progress = db.scalar(select(StudentProgression).where(StudentProgression.student_id == student_id, StudentProgression.is_current.is_(True)))
        blueprint = db.get(AssessmentBlueprint, payload.blueprintId) if payload.blueprintId else db.scalar(
            select(AssessmentBlueprint).where(AssessmentBlueprint.status == "published",
                AssessmentBlueprint.subject_id == payload.subjectId,
                AssessmentBlueprint.grade == (progress.grade if progress else -1),
                AssessmentBlueprint.term == (progress.term if progress else -1)).order_by(AssessmentBlueprint.created_at))
        if not blueprint or blueprint.status != "published" or blueprint.subject_id != payload.subjectId or not progress or (blueprint.grade, blueprint.term) != (progress.grade, progress.term):
            raise DomainError("blueprint_not_eligible", "This blueprint is not available for the student's current grade and term.", 403)
        selected = _choose(candidates, blueprint.question_count, blueprint.target_marks, str(student_id))
        if not selected: raise DomainError("question_pool_shortage", "The eligible question pool cannot satisfy this blueprint without broadening the syllabus.", 409,
            [{"eligibleQuestions": len(candidates), "eligibleMarks": sum(row[0].marks for row in candidates), "requiredQuestions": blueprint.question_count, "requiredMarks": blueprint.target_marks}])
        duration, target, title = blueprint.duration_minutes, blueprint.target_marks, blueprint.name
    elif payload.mode == "official_paper":
        paper_version = db.scalar(select(OfficialMaterialVersion).where(OfficialMaterialVersion.document_id == payload.paperId,
            OfficialMaterialVersion.kind == "past_paper", OfficialMaterialVersion.status == "published", OfficialMaterialVersion.subject_id == payload.subjectId)) if payload.paperId else None
        all_questions = db.scalars(select(OfficialQuestionVersion).where(OfficialQuestionVersion.material_version_id == paper_version.id)).all() if paper_version else []
        selected = [row for row in candidates if paper_version and row[1].id == paper_version.id]
        if not paper_version or not all_questions or len(selected) != len(all_questions):
            raise DomainError("official_paper_not_eligible", "Every question in an official paper must be within the student's covered units.", 409)
        target = sum(row[0].marks for row in selected); duration = max(1, round(target * 1.5)); title = "Official past paper"
    else:
        selected = _choose(candidates, 1, 0, str(student_id))
        if not selected: raise DomainError("question_pool_shortage", "No eligible practice question is available for the covered units.", 409)
        target, duration, title = selected[0][0].marks, 20, "Individual practice"
    ref = f"assessment:{uuid.uuid4()}"; curriculum = snapshot(db, ref, student_id, payload.subjectId); started = _now()
    assessment = Assessment(student_id=student_id, subject_id=payload.subjectId, mode=payload.mode.value,
        blueprint_id=blueprint.id if blueprint else None, official_paper_version_id=paper_version.id if paper_version else None,
        curriculum_snapshot_id=curriculum.id, title=title, target_marks=target, duration_minutes=duration,
        skills=blueprint.skills if blueprint else [], difficulty_profile=blueprint.difficulty_profile if blueprint else {},
        started_at=started, ends_at=started + timedelta(minutes=duration))
    db.add(assessment); db.flush()
    for sequence, (question, material, units) in enumerate(selected, 1):
        db.add(AssessmentQuestion(assessment_id=assessment.id, sequence=sequence, source_question_version_id=question.id,
            source_document_version_id=material.source_document_version_id, question_number=question.question_number,
            prompt=question.prompt, shared_stem=question.shared_stem, marks=question.marks, equations=question.equations,
            asset_ids=question.asset_ids, source_locations=question.source_locations, rubric=_rubric(db, material.id, question.question_number),
            unit_ids=[str(value) for value in units], unit_weights=_unit_weights(db, question.id, units),
            skills=blueprint.skills if blueprint else [], difficulty="mixed"))
    db.commit(); db.refresh(assessment); return response(db, assessment)

def _owned(db, principal, assessment_id, lock=False):
    query = select(Assessment).where(Assessment.id == assessment_id, Assessment.student_id == principal.user.id)
    row = db.scalar(query.with_for_update() if lock else query)
    if not row: raise DomainError("assessment_not_found", "Assessment not found.", 404)
    return row

def response(db, row):
    if row.status == "active" and row.ends_at <= _now(): row.status = "expired"; db.commit(); db.refresh(row)
    visible = row.status in {"submitted", "expired"}
    questions = db.scalars(select(AssessmentQuestion).where(AssessmentQuestion.assessment_id == row.id).order_by(AssessmentQuestion.sequence)).all()
    answers = {answer.question_id: answer for answer in db.scalars(select(AssessmentAnswer).where(AssessmentAnswer.assessment_id == row.id)).all()}
    results = assessment_marking.latest_results(db, row.id) if visible else {}
    return AssessmentResponse(id=row.id, studentId=row.student_id, subjectId=row.subject_id, mode=row.mode, status=row.status,
        title=row.title, targetMarks=row.target_marks, durationMinutes=row.duration_minutes, startedAt=row.started_at,
        endsAt=row.ends_at, submittedAt=row.submitted_at, skills=row.skills, difficultyProfile=row.difficulty_profile,
        feedbackVisible=visible, questions=[AssessmentQuestionResponse(id=q.id, number=q.question_number, prompt=q.prompt,
            sharedStem=q.shared_stem, marks=q.marks, equations=q.equations, assetIds=q.asset_ids, sourceLocations=q.source_locations,
            unitIds=q.unit_ids, skills=q.skills, difficulty=q.difficulty, answer=answers[q.id].answer_text if q.id in answers else "",
            fileId=answers[q.id].file_id if q.id in answers else None, saveRevision=answers[q.id].save_revision if q.id in answers else 0,
            rubric=q.rubric if visible else None,
            result=assessment_marking.result_response(results[q.id]) if q.id in results else None) for q in questions])

def list_assessments(db, principal):
    rows = db.scalars(select(Assessment).where(Assessment.student_id == principal.user.id).order_by(Assessment.started_at.desc())).all()
    return AssessmentListResponse(assessments=[response(db, row) for row in rows])

def save_answer(db, principal, assessment_id, payload):
    row = _owned(db, principal, assessment_id, True); existing = db.get(AssessmentAnswer, (row.id, payload.questionId))
    if existing and existing.idempotency_key == payload.idempotencyKey: return response(db, row)
    if row.status != "active" or row.ends_at <= _now(): raise DomainError("assessment_deadline_passed", "The assessment deadline has passed; saved answers can still be submitted.", 409)
    question = db.get(AssessmentQuestion, payload.questionId)
    if not question or question.assessment_id != row.id: raise DomainError("assessment_question_not_found", "Question not found in this assessment.", 404)
    if payload.fileId:
        try: working = db.get(AssessmentWorkingFile, uuid.UUID(payload.fileId))
        except ValueError: working = None
        if not working or working.assessment_id != row.id or working.question_id != question.id or working.student_id != principal.user.id:
            raise DomainError("working_not_found", "Upload working for this question before attaching it to the answer.", 404)
    if existing:
        existing.answer_text, existing.file_id, existing.idempotency_key = payload.answer, payload.fileId, payload.idempotencyKey
        existing.save_revision += 1; existing.saved_at = _now()
    else: db.add(AssessmentAnswer(assessment_id=row.id, question_id=question.id, answer_text=payload.answer, file_id=payload.fileId, idempotency_key=payload.idempotencyKey))
    db.commit(); db.refresh(row); return response(db, row)

def submit(db, principal, assessment_id, key):
    row = _owned(db, principal, assessment_id, True)
    if row.submission_key:
        if row.submission_key != key: raise DomainError("assessment_already_submitted", "This assessment has already been submitted.", 409)
        return response(db, row)
    now = _now(); row.status = "submitted" if now < row.ends_at else "expired"; row.submitted_at = now; row.submission_key = key
    db.commit(); db.refresh(row); return response(db, row)

def record_hint(db, principal, assessment_id, question_id, request_key):
    row = _owned(db, principal, assessment_id, True)
    if row.status != "active" or row.ends_at <= _now():
        raise DomainError("assessment_deadline_passed", "Hints are unavailable after the assessment ends.", 409)
    if row.mode != "practice":
        raise DomainError("hints_disabled", "Hints are unavailable during mock and official papers.", 403)
    question = db.get(AssessmentQuestion, question_id)
    if not question or question.assessment_id != row.id:
        raise DomainError("assessment_question_not_found", "Question not found in this assessment.", 404)
    existing = db.scalar(select(AssessmentInteraction).where(AssessmentInteraction.assessment_id == row.id,
        AssessmentInteraction.question_id == question.id, AssessmentInteraction.request_key == request_key))
    if not existing:
        db.add(AssessmentInteraction(assessment_id=row.id, question_id=question.id,
            student_id=principal.user.id, kind="hint", request_key=request_key)); db.commit()
    count = db.scalar(select(func.count()).select_from(AssessmentInteraction).where(
        AssessmentInteraction.assessment_id == row.id, AssessmentInteraction.question_id == question.id,
        AssessmentInteraction.kind == "hint")) or 0
    hints = ["Identify the command word and what the marks require.",
        "Write one relevant fact or method step, then connect it to the question.",
        "Check each step, unit and conclusion against the information given."]
    return {"hint": hints[min(count - 1, len(hints) - 1)], "total": len(hints)}

def authorize_asset(db, principal, assessment_id, asset_id):
    row = _owned(db, principal, assessment_id)
    questions = db.scalars(select(AssessmentQuestion).where(AssessmentQuestion.assessment_id == row.id)).all()
    if not any(str(asset_id) in question.asset_ids for question in questions):
        raise DomainError("assessment_asset_not_found", "Assessment asset not found.", 404)
    material = db.get(OfficialMaterialVersion, row.official_paper_version_id) if row.official_paper_version_id else None
    if not material:
        source = questions[0].source_question_version_id if questions else None
        question = db.get(OfficialQuestionVersion, source) if source else None
        material = db.get(OfficialMaterialVersion, question.material_version_id) if question else None
    if not material: raise DomainError("assessment_asset_not_found", "Assessment asset not found.", 404)
    return material.document_id
