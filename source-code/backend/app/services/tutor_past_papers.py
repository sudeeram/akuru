"""Deterministic chat tools over explicitly released, approved exam subparts.

No model selects evidence or invents official answers. Assessment storage, drawing
uploads, marking and mastery remain the existing authoritative implementations.
"""
import hashlib
import json
import random
import re
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.config import Settings
from app.errors import DomainError
from app.models import (Assessment, AssessmentInteraction, AssessmentQuestion, AuditEvent,
    Document, DocumentAsset, DocumentPage, DocumentVersion, OfficialPaperReviewQuestion,
    OfficialPaperReviewWorkspace, StudentSubject, TextbookTopic, TextbookTopicContentVersion,
    TutorPaperRelease, TutorPaperChatRequest, TutorPractice, Textbook)
from app.schemas.official_paper_reviews import ReviewQuestionData
from app.schemas.tutor_past_papers import PastPaperChatState
from app.services import assessments, curriculum_plans, official_paper_reviews, tutor_practice
from app.services.assessment_access import TutorCapability, require_tutor_access


def fingerprint(question, workspace):
    return hashlib.sha256(json.dumps({"revision": question.revision, "data": question.review_data,
        "status": question.status, "paper": str(workspace.paper_version_id),
        "scheme": str(workspace.scheme_version_id), "report": str(workspace.report_version_id)},
        sort_keys=True).encode()).hexdigest()


def release_fingerprint(question, workspace, publications, evidence_hash):
    return hashlib.sha256(json.dumps({'source': fingerprint(question, workspace),
        'publications': publications, 'evidence': evidence_hash}, sort_keys=True).encode()).hexdigest()


def topic_publications(db, workspace, part):
    paper = db.get(Document, workspace.paper_document_id)
    rows = db.execute(select(TextbookTopic, TextbookTopicContentVersion).join(
        Textbook, Textbook.id == TextbookTopic.textbook_id).join(
        TextbookTopicContentVersion, TextbookTopicContentVersion.topic_id == TextbookTopic.id).where(
        TextbookTopic.public_ref.in_(part.topicRefs), TextbookTopic.status == 'published',
        Textbook.status == 'published', TextbookTopicContentVersion.status == 'published',
        TextbookTopic.course_id == paper.course_id, TextbookTopic.subject_id == paper.subject_id)).all()
    if not part.topicRefs or len(rows) != len(set(part.topicRefs)) or len({t.public_ref for t,v in rows}) != len(rows):
        raise DomainError('practice_publication_required', 'Every mapped topic needs one current published textbook/content version.', 409)
    return sorted([dict(topicRef=t.public_ref, publicationId=str(v.id)) for t,v in rows], key=lambda v:v['topicRef'])


def _live(db, release):
    q = db.get(OfficialPaperReviewQuestion, release.question_id)
    w = db.get(OfficialPaperReviewWorkspace, q.workspace_id) if q else None
    if not release.enabled or not q or not w:
        return False
    try:
        _data, _part, publications, evidence_hash = validate_release(db, w, q, release.part_label,
            require_curriculum=release.snapshot.get('releasePolicy') == 'auto-tutor-release-v1')
        if release_fingerprint(q, w, publications, evidence_hash) != release.fingerprint:
            return False
    except DomainError:
        return False
    try:
        official_paper_reviews._validate_bound_versions(db, w)
    except DomainError:
        return False
    for asset_id in release.snapshot['sharedVisuals'] + release.snapshot['part']['visualAssetIds']:
        visual = db.get(DocumentAsset, uuid.UUID(asset_id))
        if not visual or not visual.asset_metadata.get('reviewApproved'):
            return False
    for version_id in [w.paper_version_id, w.scheme_version_id, w.report_version_id]:
        if version_id:
            version = db.get(DocumentVersion, version_id)
            document = db.get(Document, version.document_id) if version else None
            if not document or document.removed_at:
                return False
    return True


def manually_adjudicated(db, question, part, analysis):
    if not analysis or part.status != 'approved':
        return False
    return bool(db.scalar(select(AuditEvent.id).where(
        AuditEvent.action == 'official_review.part_manually_approved',
        AuditEvent.target_id == str(question.id),
        AuditEvent.event_data['part'].as_string() == part.label,
        AuditEvent.event_data['contentHash'].as_string() == analysis.content_hash,
        AuditEvent.event_data['analysisId'].as_string() == str(analysis.id),
        AuditEvent.created_at >= analysis.created_at).limit(1)))


def validate_release(db, workspace, question, label, *, require_curriculum=False):
    """Shared manual/automatic/access validator; isolate a self-contained part safely."""
    from .question_auto_approval import current_accuracy
    from . import paper_curriculum
    official_paper_reviews._validate_bound_versions(db, workspace)
    data = ReviewQuestionData.model_validate(question.review_data)
    part = next((p for p in data.parts if p.label == label), None)
    if question.status in {'excluded', 'needs_correction'} or not part or part.status not in {'approved', 'ai_approved'} or part.coverage != 'supported':
        raise DomainError('practice_review_required', 'Approve the supported subpart and resolve explicit question blockers.', 409)
    analysis = current_accuracy(db, workspace, question)
    assessed = next((p for p in analysis.analysis_data['parts'] if p['label'] == label), None) if analysis else None
    if part.status == 'ai_approved' or require_curriculum or question.status not in {'approved', 'ai_approved'}:
        if not assessed or (assessed['percent'] <= 75 and not manually_adjudicated(db, question, part, analysis)):
            raise DomainError('practice_accuracy_required', 'A current subpart assessment above 75%, or an explicit subsequent human adjudication, is required.', 409)
    if require_curriculum and not assessed.get('selfContained'):
        raise DomainError('practice_dependency_review', 'The final assessment must confirm independent answerability.', 409)
    if require_curriculum:
        check = assessed.get('curriculum') if assessed else None
        if not check or not check.get('accepted') or not paper_curriculum.current(db, part.model_dump(mode='json'), check):
            raise DomainError('practice_curriculum_required', 'Reassess current published textbook evidence and resolve mapping uncertainty.', 409)
    if re.search(r'using (?:your|the) (?:answer|result)|(?:answer|result) (?:to|from) (?:part|\()', part.prompt, re.I):
        raise DomainError('practice_dependency_review', 'Release only self-contained subparts with all required information.', 409)
    if part.assessmentReadiness not in {'automatic', 'manual_only'} or (part.assessmentReadiness == 'manual_only' and part.responseType != 'drawing'):
        raise DomainError('practice_marking_not_ready', 'Confirm automatic marking or supported manual drawing review first.', 409)
    if not part.topicRefs or not part.markingPoints or not any(v.blockId for v in part.schemeSources):
        raise DomainError('practice_evidence_required', 'Exact scheme evidence and published topic mappings are required.', 409)
    if sum(p.marks for p in data.parts) != data.marks or data.candidateVisualAssetIds:
        raise DomainError('practice_shared_context_required', 'Resolve question totals and unassigned visuals before release.', 409)
    # Validate the actual shared context plus this part against all normal approval
    # gates. Unrelated siblings cannot block independent parts, nor hide shared defects.
    scoped = data.model_copy(deep=True)
    scoped.parts = [part.model_copy(deep=True)]
    scoped.marks = part.marks
    scoped.parts[0].status = 'approved'
    official_paper_reviews._validate_question(db, workspace, 'approved', scoped, question.review_data, question.number)
    from .official_question_analyses import content_hash, source_manifest
    return data, part, topic_publications(db, workspace, part), content_hash(db, question, source_manifest(db, workspace))


def release_part(db, principal, paper_id, number, payload, *, automatic=False, commit=True):
    w = official_paper_reviews._workspace(db, paper_id)
    official_paper_reviews._validate_bound_versions(db, w)
    q = db.scalar(select(OfficialPaperReviewQuestion).where(
        OfficialPaperReviewQuestion.workspace_id == w.id, OfficialPaperReviewQuestion.number == number).with_for_update())
    if not q or q.revision != payload.revision:
        raise DomainError('practice_review_changed', 'Reload the question: its review has changed.', 409)
    if not payload.enabled:
        rows = db.scalars(select(TutorPaperRelease).where(TutorPaperRelease.question_id == q.id,
            TutorPaperRelease.part_label == payload.partLabel)).all()
        for row in rows: row.enabled = False
        db.add(AuditEvent(created_at=datetime.now(timezone.utc), actor_id=principal.user.id, action='tutor_paper.withdrawn', target_type='question',
            target_id=str(q.id), event_data={'part': payload.partLabel}))
        if commit: db.commit()
        return {'enabled': False, 'partLabel': payload.partLabel}
    if not payload.confirmSelfContained:
        raise DomainError('practice_dependency_review', 'Confirm this part is self-contained.', 409)
    data, part, publications, evidence_hash = validate_release(db, w, q, payload.partLabel, require_curriculum=automatic)
    last_decision = db.scalar(select(AuditEvent).where(
        AuditEvent.target_id == str(q.id), AuditEvent.action.in_(['tutor_paper.withdrawn', 'tutor_paper.released']),
        AuditEvent.event_data['part'].as_string() == part.label).order_by(AuditEvent.created_at.desc()).limit(1))
    withdrawn_current = db.scalar(select(TutorPaperRelease.id).where(TutorPaperRelease.question_id == q.id, TutorPaperRelease.part_label == part.label, TutorPaperRelease.fingerprint == release_fingerprint(q, w, publications, evidence_hash), TutorPaperRelease.enabled.is_(False)))
    if automatic and (withdrawn_current or (last_decision and last_decision.action == 'tutor_paper.withdrawn')):
        raise DomainError('practice_explicit_withdrawal', 'An Admin withdrew this part. Explicitly re-enable it first.', 409)
    from .question_auto_approval import current_accuracy
    paper = db.get(Document, w.paper_document_id)
    source_hash = release_fingerprint(q, w, publications, evidence_hash)
    row = db.scalar(select(TutorPaperRelease).where(TutorPaperRelease.question_id == q.id,
        TutorPaperRelease.part_label == part.label, TutorPaperRelease.fingerprint == source_hash))
    if not row:
        row = TutorPaperRelease(question_id=q.id, part_label=part.label, revision=q.revision,
            fingerprint=source_hash, released_by=principal.user.id, snapshot={
                'paperId': str(paper.id), 'paperVersionId': str(w.paper_version_id),
                'schemeId': str(w.scheme_document_id), 'schemeVersionId': str(w.scheme_version_id),
                'reportId': str(w.report_document_id) if w.report_document_id else None,
                'reportVersionId': str(w.report_version_id) if w.report_version_id else None,
                'paperTitle': paper.title, 'subjectId': paper.subject_id,
                'component': paper.component, 'year': paper.publication_year, 'session': paper.exam_session,
                'number': q.number, 'sharedStem': data.sharedStem,
                'sharedVisuals': [str(v) for v in data.visualAssetIds],
                'part': part.model_dump(mode='json'), 'selfContainedConfirmed': True,
                'sourceFingerprint': fingerprint(q, w), 'topicPublications': publications, 'evidenceContentHash': evidence_hash,
                'releasePolicy': 'auto-tutor-release-v1' if automatic else 'manual',
                'curriculum': next((p.get('curriculum') for p in current_accuracy(db, w, q).analysis_data['parts'] if p['label'] == part.label), None) if automatic else None})
        db.add(row)
    if row.enabled and row.id is not None:
        return {'releaseId': str(row.id), 'partLabel': part.label, 'enabled': True}
    row.enabled = True
    db.flush()
    db.add(AuditEvent(created_at=datetime.now(timezone.utc), actor_id=principal.user.id, action='tutor_paper.released', target_type='question',
        target_id=str(q.id), event_data={'part': part.label, 'releaseId': str(row.id), 'sourceHash': source_hash, 'origin': 'automatic' if automatic else 'manual',
            'policy': 'auto-tutor-release-v1' if automatic else 'manual'}))
    if commit: db.commit()
    return {'releaseId': str(row.id), 'partLabel': part.label, 'enabled': True}


def auto_release(db, principal, workspace, question):
    """Same transaction as the final assessment; no model calls or implicit retries."""
    from app.schemas.tutor_past_papers import ReleasePastPaperPart
    results = []
    for part in question.review_data['parts']:
        try:
            value = release_part(db, principal, workspace.paper_document_id, question.number,
                ReleasePastPaperPart(partLabel=part['label'], revision=question.revision,
                    confirmSelfContained=True), automatic=True, commit=False)
            results.append(dict(part=part['label'], **value))
        except DomainError as exc:
            results.append(dict(part=part['label'], enabled=False, code=exc.code, reason=exc.message))
    return results


def retry_auto_releases(db, principal, paper_id):
    """Recover release writes using saved current assessments; never call a model."""
    workspace = official_paper_reviews._workspace(db, paper_id)
    questions = db.scalars(select(OfficialPaperReviewQuestion).where(
        OfficialPaperReviewQuestion.workspace_id == workspace.id).with_for_update()).all()
    results = [dict(number=q.number, parts=auto_release(db, principal, workspace, q)) for q in questions]
    db.commit()
    return {'policy': 'auto-tutor-release-v1', 'results': results}


def release_readiness(db, paper_id):
    workspace = official_paper_reviews._workspace(db, paper_id)
    result = []
    for question in db.scalars(select(OfficialPaperReviewQuestion).where(
            OfficialPaperReviewQuestion.workspace_id == workspace.id)):
        for part in question.review_data['parts']:
            try:
                validate_release(db, workspace, question, part['label'])
                result.append(dict(number=question.number, partLabel=part['label'], ready=True, blocker=None))
            except DomainError as exc:
                result.append(dict(number=question.number, partLabel=part['label'], ready=False, blocker=exc.message))
    return result


def admin_releases(db, paper_id):
    w = official_paper_reviews._workspace(db, paper_id)
    rows = db.scalars(select(TutorPaperRelease).join(OfficialPaperReviewQuestion,
        OfficialPaperReviewQuestion.id == TutorPaperRelease.question_id).where(OfficialPaperReviewQuestion.workspace_id == w.id)).all()
    return [{'releaseId': str(r.id), 'number': r.snapshot['number'], 'partLabel': r.part_label,
             'enabled': r.enabled, 'current': _live(db, r)} for r in rows]


def require_access(db, settings, principal, session):
    # This channel has its own explicit audience switch. It does not broaden the text pilot.
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TEXT,
        session.subject_id, 'tutor_text', topic_id=session.active_topic_id)
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS,
        session.subject_id, 'tutor_tools', topic_id=session.active_topic_id)
    if not settings.tutor_past_paper_chat_enabled or principal.user.id not in settings.tutor_past_paper_chat_student_ids:
        raise DomainError('past_paper_chat_not_released', 'Past-paper chat is not enabled for your account yet.', 403)
    if not db.get(StudentSubject, (principal.user.id, session.subject_id)):
        raise DomainError('subject_not_enrolled', 'Choose one of your enrolled subjects.', 403)


def eligible(db, student_id, subject_id):
    coverage = curriculum_plans.student_coverage(db, student_id, subject_id)
    if coverage.status != 'ready':
        raise DomainError('assessment_coverage_not_ready', coverage.message, 409)
    allowed = {p.topicRef for p in coverage.coveredTopics}
    published = set(db.scalars(select(TextbookTopic.public_ref).join(TextbookTopicContentVersion,
        TextbookTopicContentVersion.topic_id == TextbookTopic.id).where(TextbookTopic.status == 'published',
        TextbookTopic.subject_id == subject_id, TextbookTopicContentVersion.status == 'published')).all())
    return [r for r in db.scalars(select(TutorPaperRelease).join(OfficialPaperReviewQuestion, OfficialPaperReviewQuestion.id==TutorPaperRelease.question_id).where(TutorPaperRelease.enabled.is_(True),TutorPaperRelease.snapshot['subjectId'].as_string()==subject_id,TutorPaperRelease.revision==OfficialPaperReviewQuestion.revision)).all()
        if r.snapshot['subjectId'] == subject_id and set(r.snapshot['part']['topicRefs']).issubset(allowed & published)
        and r.snapshot['part']['topicRefs'] and _live(db, r)]


def _practice(db, session):
    return db.scalar(select(TutorPractice).join(AssessmentQuestion, AssessmentQuestion.id == TutorPractice.question_id)
        .join(Assessment, Assessment.id == TutorPractice.assessment_id).where(TutorPractice.session_id == session.id, AssessmentQuestion.tutor_paper_release_id.is_not(None))
        .order_by(Assessment.started_at.desc(), TutorPractice.created_at.desc()))


def _release_for_practice(db, settings, principal, session, practice):
    require_access(db, settings, principal, session)
    question = db.get(AssessmentQuestion, practice.question_id)
    release = db.get(TutorPaperRelease, question.tutor_paper_release_id)
    if release.id not in {r.id for r in eligible(db, principal.user.id, session.subject_id)}:
        raise DomainError('practice_source_unavailable', 'This practice source has changed or is no longer available. Ask for another question.', 409)
    return release, question


def state(db, settings, principal, session):
    practice = _practice(db, session)
    if not practice: return None
    release, question = _release_for_practice(db, settings, principal, session, practice)
    assessment = db.get(Assessment, practice.assessment_id)
    revealed = bool(db.scalar(select(AssessmentInteraction.id).where(AssessmentInteraction.assessment_id == assessment.id,
        AssessmentInteraction.question_id == question.id, AssessmentInteraction.kind == 'worked_answer')))
    visible = revealed or bool(assessment.submitted_at)
    result = tutor_practice._response(db, practice)
    if visible:
        result.question = result.question.model_copy(update={'rubric': question.rubric})
    else:
        result.question = result.question.model_copy(update={'generatedWorkedAnswerAvailable': False})
    sources = []
    snap = release.snapshot
    for kind, version_key, source_key in [('Paper','paperVersionId','paperSources'),
        ('Marking scheme','schemeVersionId','schemeSources'), ('Examiner report','reportVersionId','reportSources')]:
        if kind != 'Paper' and not visible: continue
        version_id = snap.get(version_key)
        for page_number in sorted({s['page'] for s in snap['part'].get(source_key, [])}):
            page = db.scalar(select(DocumentPage).where(DocumentPage.document_version_id == uuid.UUID(version_id),
                DocumentPage.page_number == page_number)) if version_id else None
            if page and page.render_asset_id:
                sources.append({'label': f'{kind} · Page {page_number}',
                    'url': f'/api/v1/tutoring/sessions/{session.public_ref}/past-paper/assets/{page.render_asset_id}'})
    return PastPaperChatState(practice=result, paperTitle=snap['paperTitle'],
        questionLabel=f"{snap['number']}({release.part_label})", answerRevealed=revealed,
        markingGuidance=question.rubric['markingPoints'] if visible else [],
        alternatives=question.rubric.get('alternatives', []) if visible else [],
        examinerAdvice=question.rubric.get('examinerAdvice', []) if visible else [], sources=sources,
        state='answered' if assessment.submitted_at and not revealed else 'revealed' if revealed
            else 'expired' if assessment.ends_at <= datetime.now(timezone.utc) else 'awaiting_answer')


def identity(message):
    component = re.search(r"\b([12](?:HB|[BCP])R?)\b", message, re.I)
    year = re.search(r"\b(20\d{2})\b", message)
    month = re.search(r"\b(january|june|november)\b", message, re.I)
    number = re.search(r"\b(?:question|q)\s*(\d{1,2})(?!\d)", message, re.I)
    tail = message[number.end():] if number else ""
    part = re.match(r"\s*(?:part\s+)?(?:\(([a-z])\)|([a-z])\b)(?:\s*\(([ivx]+)\))?", tail, re.I)
    if not part:
        part = re.search(r"\bpart\s+(?:\(([a-z])\)|([a-z])\b)(?:\s*\(([ivx]+)\))?", message, re.I)
    label = ((part[1] or part[2]).lower() + (f"({part[3].lower()})" if part[3] else "")) if part else None
    return {'component': component[1].upper() if component else None, 'year': int(year[1]) if year else None,
        'session': month[1].lower() if month else None, 'number': number[1] if number else None, 'part': label}


def select_question(db, settings, principal, session, key, message):
    require_access(db, settings, principal, session)
    pool = eligible(db, principal.user.id, session.subject_id)
    # Only exact identity filters; never silently substitute a different component/session.
    requested = identity(message)
    subject_text = re.sub(r'human[ -]biology', 'human_biology', message, flags=re.I)
    for subject, canonical in [('maths','maths'),('mathematics','maths'),('human_biology','human-biology'),('physics','physics'),('biology','biology'),('english','english'),('french','french'),('ict','ict'),('chemistry','chemistry')]:
        if re.search(rf'\b{subject}\b', subject_text, re.I) and canonical != session.subject_id:
            raise DomainError('practice_subject_mismatch', 'Start a Tutor session in the requested enrolled subject first.', 409)
    for field in ['component', 'year', 'session', 'number']:
        if requested[field] is not None:
            pool = [r for r in pool if str(r.snapshot.get(field, '')).lower() == str(requested[field]).lower()]
    if requested['part']:
        pool = [r for r in pool if r.part_label == requested['part']]
    elif requested['number'] and len(pool) > 1:
        raise DomainError('practice_question_ambiguous', 'Choose a subpart: ' + ', '.join(f"{r.snapshot['component']} Q{r.snapshot['number']}({r.part_label})" for r in pool[:12]), 409)
    if not pool:
        raise DomainError('practice_question_unavailable', 'No released past-paper question matches within your published, covered topics. Try asking for any available question in this subject, or ask Admin to release more reviewed items.', 409)
    replay = db.scalar(select(TutorPractice).where(TutorPractice.session_id == session.id, TutorPractice.request_key == key))
    if replay: return state(db, settings, principal, session)
    active = db.scalar(select(Assessment).where(Assessment.student_id == principal.user.id, Assessment.status == 'active'))
    old = _practice(db, session)
    if active and (not old or old.assessment_id != active.id):
        raise DomainError('assessment_already_active', 'Finish your other active assessment first.', 409)
    if old and old.status == 'active' and active and active.ends_at > datetime.now(timezone.utc):
        raise DomainError('practice_answer_pending', 'Answer the current question or choose Show approved answer before asking for another.', 409)
    if active:
        active.status = 'expired'
    if old and old.status == 'active': old.status = 'submitted'
    seen = set(db.scalars(select(AssessmentQuestion.tutor_paper_release_id).join(Assessment,
        Assessment.id == AssessmentQuestion.assessment_id).where(Assessment.student_id == principal.user.id)).all())
    unseen = [r for r in pool if r.id not in seen]
    candidates = unseen or [r for r in pool if not old or r.id != db.get(AssessmentQuestion, old.question_id).tutor_paper_release_id] or pool
    release = random.SystemRandom().choice(candidates)
    snap, part = release.snapshot, release.snapshot['part']
    topics = db.scalars(select(TextbookTopic).where(TextbookTopic.public_ref.in_(part['topicRefs']))).all()
    snapshot = curriculum_plans.snapshot(db, f'tutor-paper:{uuid.uuid4()}', principal.user.id, session.subject_id)
    now = datetime.now(timezone.utc)
    assessment = Assessment(student_id=principal.user.id, subject_id=session.subject_id, mode='practice',
        title=f"{snap['component']} Q{snap['number']}({release.part_label})", target_marks=part['marks'],
        duration_minutes=60, started_at=now, ends_at=now + timedelta(hours=1), curriculum_snapshot_id=snapshot.id)
    db.add(assessment); db.flush()
    ids = list(dict.fromkeys(snap['sharedVisuals'] + part['visualAssetIds']))
    rubric = {'markingPoints': part['markingPoints'], 'scoringRules': part['scoringRules'],
        'alternatives': part['alternatives'], 'examinerAdvice': [part['examinerAdvice']] if part['examinerAdvice'] and part['reportSources'] else [],
        'commonMistakes': [], 'answerVisuals': part.get('answerVisuals', []),
        'drawingParts': [part['label']] if part['responseType'] == 'drawing' else [],
        'tutorSessionRef': session.public_ref, 'releaseId': str(release.id), 'sourceHash': release.fingerprint}
    question = AssessmentQuestion(assessment_id=assessment.id, sequence=1, tutor_paper_release_id=release.id,
        source_document_version_id=uuid.UUID(snap['paperVersionId']), question_number=f"{snap['number']}({part['label']})",
        prompt=part['prompt'], shared_stem=snap['sharedStem'], marks=part['marks'], equations=[], asset_ids=ids,
        source_locations=part['paperSources'], rubric=rubric, topic_ids=[str(t.id) for t in topics],
        topic_weights={str(t.id): 100 // len(topics) + (1 if i < 100 % len(topics) else 0) for i,t in enumerate(topics)})
    db.add(question); db.flush()
    row = TutorPractice(public_ref=f'tutor_practice_{uuid.uuid4().hex}', session_id=session.id,
        student_id=principal.user.id, subject_id=session.subject_id, topic_id=topics[0].id,
        assessment_id=assessment.id, question_id=question.id, request_key=key)
    db.add(row); db.commit()
    return state(db, settings, principal, session)


def reveal(db, settings, principal, session, key):
    row = _practice(db, session)
    if not row: raise DomainError('practice_not_started', 'Ask for a past-paper question first.', 409)
    release, question = _release_for_practice(db, settings, principal, session, row)
    assessment = db.get(Assessment, row.assessment_id)
    if not assessment.submitted_at and not db.scalar(select(AssessmentInteraction.id).where(AssessmentInteraction.assessment_id == assessment.id,
        AssessmentInteraction.question_id == question.id, AssessmentInteraction.kind == 'worked_answer')):
        db.add(AssessmentInteraction(assessment_id=assessment.id, question_id=question.id, student_id=principal.user.id,
            kind='worked_answer', request_key='chat-approved-answer-reveal'))
    # A reveal is assisted practice, never a fake submitted answer or a mastery result.
    if assessment.status == 'active': assessment.status = 'expired'
    row.status = 'submitted'
    db.commit()
    return state(db, settings, principal, session)


def authorize_assessment(db, settings, principal, assessment):
    questions = db.scalars(select(AssessmentQuestion).where(AssessmentQuestion.assessment_id == assessment.id,
        AssessmentQuestion.tutor_paper_release_id.is_not(None))).all()
    if not questions: return
    from app.services import tutor_sessions
    for question in questions:
        session = tutor_sessions._owned_session(db, principal.user.id, question.rubric['tutorSessionRef'])
        require_access(db, settings, principal, session)
        release = db.get(TutorPaperRelease, question.tutor_paper_release_id)
        if release.id not in {r.id for r in eligible(db, principal.user.id, assessment.subject_id)}:
            raise DomainError('practice_source_unavailable', 'This practice source is no longer available.', 409)


def asset(db, settings, principal, session, asset_id):
    require_access(db, settings, principal, session)
    current = state(db, settings, principal, session)
    if not current: raise DomainError('practice_asset_not_found', 'Source not found.', 404)
    allowed = set(current.practice.question.assetIds)
    for source in current.sources: allowed.add(source['url'].rsplit('/',1)[-1])
    if str(asset_id) not in allowed: raise DomainError('practice_asset_not_found', 'Source not found.', 404)
    return db.get(DocumentAsset, asset_id)


def intent(message, active=False):
    text = message.strip().lower()
    if text in {'return to textbook', 'stop past-paper practice', 'stop practice'}: return 'stop'
    if re.search(r'\b(mock|timed|full exam)\b', text): return 'mock'
    if re.search(r'\b(show|reveal|see|give|explain|what)\b.*\b(answer|marking|mark scheme|examiner)\b', text): return 'reveal'
    if re.search(r'\bhint\b', text): return 'hint'
    if re.search(r'\b(next|another)\s+(?:past[- ]paper\s+)?question\b', text): return 'select'
    if re.search(r'\b(?:question|q)\s*\d', text) or ('paper' in text and re.search(r'\b(ask|question|practi[cs]e|discuss|help|available)\b', text)):
        return 'select'
    if text in {'return to textbook', 'stop past-paper practice', 'stop practice'}: return 'stop'
    if text.startswith(('my answer:', 'answer:')): return 'answer'
    if active and (not re.search(r'\?|^(?:why|how|what|can|explain|tell)\b', text)):
        return 'answer'
    if active: return 'help'
    return None


def handle(db, settings, principal, session, payload, generator=None):
    """Return None only when this is an ordinary textbook-teaching turn."""
    from app.repositories import tutor_agent as repository
    from app.schemas.tutor_agent import TutorAgentTurnResponse, TutorToolResult
    from app.schemas.assessments import AnswerSave
    from app.services import tutor_agent, assessment_marking
    previous = _practice(db, session)
    action = intent(payload.message, active=bool(previous and previous.status == 'active'))
    if action is None:
        # Follow-ups about a completed exam question remain in the exam workflow.
        if previous and re.search(r'\b(mark scheme|examiner|this question|that question|my answer|lose marks|lost marks|my marks|my response)\b', payload.message, re.I):
            action = 'help'
        else: return None
    # A durable claim survives helper/provider commits. Concurrent retries cannot
    # run the same question selection, submission or paid marking twice.
    claimed = db.execute(insert(TutorPaperChatRequest).values(session_id=session.id,
        request_key=payload.requestKey).on_conflict_do_nothing().returning(TutorPaperChatRequest.request_key)).scalar()
    if not claimed:
        existing = repository.replay(db, session.id, payload.requestKey)
        if existing:
            return TutorAgentTurnResponse.model_validate(existing.response_data)
        raise DomainError('practice_request_pending', 'This request is processing or was interrupted. Reload your practice before sending another request.', 409)
    db.commit()
    operation = uuid.uuid4()
    current = None
    choices = ['Ask me a past-paper question']
    try:
        require_access(db, settings, principal, session)
        requested = identity(payload.message)
        if previous and action in {'reveal', 'hint', 'answer', 'help'}:
            reference = db.get(TutorPaperRelease, db.get(AssessmentQuestion, previous.question_id).tutor_paper_release_id)
            mismatch = any(requested[f] is not None and str(requested[f]).lower() != str(reference.snapshot.get(f, '')).lower()
                for f in ['component', 'year', 'session', 'number']) or (requested['part'] is not None and requested['part'] != reference.part_label)
            if mismatch:
                raise DomainError('practice_reference_mismatch', 'That names a different question or subpart. Finish the current item, then ask to discuss the specific paper and subpart before revealing its answer.', 409)
        if action == 'mock':
            content = 'Full mock exams are not available through this chat yet. I can help you practise released past-paper questions one at a time.'
        elif action == 'stop':
            if previous:
                _release_for_practice(db, settings, principal, session, previous)
                assessment = db.get(Assessment, previous.assessment_id)
                if assessment.status == 'active': assessment.status = 'expired'
                previous.status = 'submitted'
                db.commit()
            content = 'Past-paper practice stopped. No marks have been awarded for an abandoned answer. You can ask a textbook question now.'
        elif action == 'select':
            if re.search(r'\b(?:list|available)\b', payload.message, re.I):
                titles = sorted({r.snapshot['paperTitle'] for r in eligible(db, principal.user.id, session.subject_id)})
                content = 'Available released practice sources:\n\n' + '\n'.join(titles) if titles else 'No approved practice items have been released for your covered topics yet.'
            else:
                current = select_question(db, settings, principal, session, payload.requestKey, payload.message)
                q = current.practice.question
                content = f"**{current.paperTitle} · Q{current.questionLabel} · {q.marks} marks**\n\n" + (q.sharedStem + '\n\n' if q.sharedStem else '') + q.prompt + '\n\nType your answer here. You can ask for a hint or choose Show approved answer.'
                choices = ['Give me a hint', 'Show approved answer', 'Stop past-paper practice']
        elif action == 'reveal':
            current = reveal(db, settings, principal, session, payload.requestKey)
            content = '**Approved marking guidance**\n\n' + '\n\n'.join(p['text'] for p in current.markingGuidance)
            if current.alternatives: content += '\n\n**Accepted alternatives and instructions**\n\n' + '\n\n'.join(current.alternatives)
            if current.examinerAdvice: content += '\n\n**Reviewed examiner guidance**\n\n' + '\n\n'.join(current.examinerAdvice)
            else: content += '\n\nNo reviewed examiner guidance is available for this item.'
            content += ('\n\nThis is assisted practice. Revealing the answer does not award marks or independent mastery.' if current.answerRevealed else '\n\nThis is reviewed marking guidance, not a newly generated official answer.')
            choices = ['Next question']
        elif action == 'answer':
            if not previous: raise DomainError('practice_not_started', 'Ask for a past-paper question first.', 409)
            _release_for_practice(db, settings, principal, session, previous)
            assessment = db.get(Assessment, previous.assessment_id)
            if assessment.submitted_at and assessment.submission_key != payload.requestKey:
                raise DomainError('practice_already_submitted', 'This answer is already submitted. Ask to see the approved answer or request another question.', 409)
            if not assessment.submitted_at:
                text = re.sub(r'^(?:my answer|answer):\s*', '', payload.message.strip(), flags=re.I)
                if not text.strip():
                    raise DomainError('practice_answer_empty', 'Type your answer after My answer: before submitting.', 422)
                assessments.save_answer(db, principal, assessment.id, AnswerSave(questionId=previous.question_id,
                    answer=text, idempotencyKey=payload.requestKey))
                assessments.submit(db, principal, assessment.id, payload.requestKey)
            previous.status = 'submitted'; previous.submitted_at = datetime.now(timezone.utc)
            db.commit()
            # Keep account routing, pinned model, per-child quota and invocation records
            # for both authoritative marking passes. No separate chat marking prompt.
            def generate(mark_db, mark_settings, request):
                request.metadata['session_ref'] = session.public_ref
                return tutor_agent._invoke(mark_db, mark_settings, principal, request, uuid.uuid4(), generator)
            try:
                assessment_marking.evaluate(db, settings, assessment, payload.requestKey, generator=generate)
                current = state(db, settings, principal, session)
                result = current.practice.question.result
                if result and result.status == 'published':
                    content = f'**Feedback · {result.awardedMarks}/{result.maxMarks} marks**\n\n{result.teachingExplanation}\n\n**How to improve**\n\n{result.improvedAnswer}'
                else:
                    content = 'Your answer is saved. Automatic feedback has not passed its release/review checks, so no score is being shown. You can still compare your answer with the approved marking guidance.'
            except DomainError as error:
                if error.status_code < 400: raise
                content = 'Your answer is saved, but automatic marking is currently unavailable. No score has been awarded. You can still show the approved marking guidance.'
                current = state(db, settings, principal, session)
            choices = ['Show approved answer', 'Next question']
        else:
            if not previous: raise DomainError('practice_not_started', 'Ask for a past-paper question first.', 409)
            _release_for_practice(db, settings, principal, session, previous)
            current = state(db, settings, principal, session)
            if action == 'hint' and current.state == 'awaiting_answer':
                hint = assessments.record_hint(db, principal, previous.assessment_id, previous.question_id, payload.requestKey)
                content = '**Hint**\n\n' + hint['hint']
            else:
                content = ('**Approved marking guidance**\n\n' + '\n\n'.join(p['text'] for p in current.markingGuidance) + ('\n\n**Reviewed examiner guidance**\n\n' + '\n\n'.join(current.examinerAdvice) if current.examinerAdvice else '') + '\n\n' if current.state in {'answered', 'revealed'} else '') + 'We are discussing the active past-paper question. Type “My answer: …” to submit your response, request a hint, or choose Show approved answer to see its reviewed marking guidance. I will not invent official marking points.'
            choices = ['Show approved answer', 'Next question'] if current.state != 'awaiting_answer' else ['Give me a hint', 'Show approved answer', 'Stop past-paper practice']
    except DomainError as error:
        if error.code in {'tutor_disabled_during_formal_assessment', 'tutor_pilot_restricted', 'subject_not_enrolled'}:
            raise
        content = error.message
    stored = TutorAgentTurnResponse(operationRef=f'tutor_operation_{operation.hex}', turnRef='pending',
        content=content, teachingMode=payload.teachingMode, pastPaper=current, followUpChoices=choices,
        toolResults=[TutorToolResult(name='past_paper_practice', status='ready' if current else 'unavailable',
            summary=f'Past-paper chat action: {action}', evidenceRefs=[current.practice.practiceRef] if current else [])],
        provider='akuru', model='approved-exam-tools-v1', promptName='past-paper-chat', promptVersion='1.0.0').model_dump(mode='json')
    turn = repository.save_exchange(db, session, payload.message.strip(), payload.requestKey, stored, [],
        operation, 'akuru', 'approved-exam-tools-v1', 'past-paper-chat', '1.0.0')
    claim = db.get(TutorPaperChatRequest, (session.id, payload.requestKey))
    claim.completed = True
    db.commit()
    tutor_agent._record_safety(db, session, turn)
    return TutorAgentTurnResponse.model_validate({**stored, 'turnRef': turn.public_ref})
