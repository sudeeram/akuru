"""Admin-only scoring regression of saved rubrics using synthetic reviewed answers."""
import hashlib
import json
import uuid
from types import SimpleNamespace
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy import select

from app.errors import DomainError
from app.models import Document, TextbookTopic, AuditEvent, User, EvidenceLinkJob
from app.schemas.official_paper_reviews import ReviewQuestionData, SaveReviewQuestion
from . import assessment_marking as marker, official_paper_reviews as reviews
from . import evidence_links, subject_marking

PASS_PREFIX = 'Scoring validation passed: '


class Sample(BaseModel):
    model_config = ConfigDict(extra='forbid')
    answer: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    expectedPoints: list[Annotated[str, StringConstraints(min_length=1, max_length=30)]] = Field(max_length=30)


class ValidateScoring(BaseModel):
    model_config = ConfigDict(extra='forbid')
    requestId: uuid.UUID
    partLabel: str = Field(min_length=1, max_length=30)
    expectedRevision: int = Field(ge=1)
    confirmReviewed: bool
    samples: list[Sample] = Field(min_length=2, max_length=8)


def rubric_hash(data, part):
    fields = part.model_dump(mode='json')
    for key in ('assessmentReadiness', 'assessmentReadinessReason', 'status', 'extractionConfidence'):
        fields.pop(key, None)
    return hashlib.sha256(json.dumps([data.sharedStem, data.prompt, fields], sort_keys=True).encode()).hexdigest()


def run(db, settings, principal, paper_id, number, payload, *, generator=None, expected_source_hash=None, job_id=None):
    workspace, row, digest = evidence_links._context(db, paper_id, number)
    evidence_links._fresh(row, digest, payload.expectedRevision, expected_source_hash or digest)
    data = ReviewQuestionData.model_validate(row.review_data)
    part = next((p for p in data.parts if p.label == payload.partLabel), None)
    if not payload.confirmReviewed or not part or part.status not in {'approved','ai_approved'} or row.status in {'excluded','needs_correction'}:
        raise DomainError('scoring_review_required', 'Approve the subpart and confirm the rubric and sample expectations were reviewed.', 409)
    if part.responseType != 'text':
        raise DomainError('scoring_unsupported_response', 'This check currently supports typed responses only.', 409)
    paper = db.get(Document, paper_id)
    subject = paper.subject_id
    question_id = row.id
    digest_rubric = rubric_hash(data, part)
    topic_ids = list(db.scalars(select(TextbookTopic.id).where(
        TextbookTopic.public_ref.in_(part.topicRefs), TextbookTopic.course_id == paper.course_id,
        TextbookTopic.subject_id == subject)))
    rubric = dict(markingPoints=[p.model_dump(mode='json') for p in part.markingPoints],
        scoringRules=part.scoringRules.model_dump(mode='json'), alternatives=part.alternatives,
        examinerAdvice=[part.examinerAdvice] if part.examinerAdvice and part.reportSources else [],
        commonMistakes=[])
    question = SimpleNamespace(rubric=rubric, marks=part.marks, topic_ids=[str(t) for t in topic_ids],
        question_number=f'{number}({part.label})', prompt=part.prompt, shared_stem=data.sharedStem,
        equations=[], source_locations=[v.model_dump(mode='json') for v in part.paperSources],
        source_question_version_id=None, tutor_paper_release_id=None, source_document_version_id=workspace.paper_version_id)
    points = marker._official_points(question)
    known = {p['pointId'] for p in points}
    expected = [set(s.expectedPoints) for s in payload.samples]
    expected_totals = [marker.marking_rules.expected_marks(ids, rubric['scoringRules']) for ids in expected]
    if (len({marker.marking_rules.normalize(s.answer) for s in payload.samples}) != len(expected)
            or any(len(ids) != len(s.expectedPoints) or not ids <= known or marker.marking_rules.expected_marks(ids, rubric["scoringRules"]) > part.marks
                   for s, ids in zip(payload.samples, expected))
            or set().union(*expected) != known or not any(not ids for ids in expected)
            or part.marks not in expected_totals
            or (part.marks > 1 and not any(0 < value < part.marks for value in expected_totals))):
        raise DomainError('scoring_fixture_coverage', 'Use distinct sample answers covering every point, zero and full credit, and partial credit where applicable.', 422)
    policy = subject_marking.policy(subject)
    sources = marker._sources(db, question, settings.assessment_context_chunks)
    prompt = marker.get_prompt('assessment')
    sources.append(dict(type='assessment_prompt',name=prompt.name,version=prompt.version,instructions=prompt.instructions))
    db.rollback()
    cases = []
    for sample, ids, expected_total in zip(payload.samples, expected, expected_totals):
        deterministic = subject_marking.analyze(subject, question.prompt, sample.answer, rubric, None)
        first, second, marks, decisions, confidence, review = marker.mark_text_answer(
            db, settings, question, SimpleNamespace(answer_text=sample.answer, file_id=None),
            points, sources, policy, deterministic, None, sample.answer,
            dict(subject_id=subject, scoring_validation='true'), generator or marker._generate)
        actual = {d.pointId for d in decisions if d.awarded}
        cases.append(dict(expectedMarks=expected_total, actualMarks=marks, expectedPoints=sorted(ids),
            actualPoints=sorted(actual), model=second.model, confidence=confidence,
            responseIds=[r.response_id for r in (first,second) if r.response_id],
            passed=marks==expected_total and actual==ids and not review
                and confidence>=max(settings.assessment_confidence_threshold, 0.90 if policy.subjective else 0)))
    db.expire_all()
    workspace, row, latest = evidence_links._context(db, paper_id, number, lock=True)
    evidence_links._fresh(row, latest, payload.expectedRevision, digest)
    actor = db.get(User, principal.user.id, populate_existing=True)
    if not actor or not actor.is_active or actor.role != "admin":
        raise DomainError("permission_denied", "Requesting Admin is inactive.", 403)
    if job_id and db.get(EvidenceLinkJob, job_id, with_for_update=True, populate_existing=True).status != "processing":
        raise DomainError("scoring_job_interrupted", "The validation job is no longer active.", 409)
    if marker._sources(db, question, settings.assessment_context_chunks) != sources[:-1]:
        raise DomainError("scoring_evidence_changed", "Textbook context changed during scoring validation.", 409)
    passed = all(c['passed'] for c in cases)
    db.add(AuditEvent(actor_id=principal.user.id, action='official_review.scoring_validated',
        target_type='official_paper_review_question', target_id=str(question_id),
        event_data=dict(part=part.label, rubricHash=digest_rubric, sourceHash=digest,
                        revision=row.revision, passed=passed, cases=cases,
                        sampleHashes=[hashlib.sha256(s.answer.encode()).hexdigest() for s in payload.samples])))
    if passed:
        part.assessmentReadiness = 'automatic'
        part.assessmentReadinessReason = f'{PASS_PREFIX}{len(cases)}/{len(cases)} reviewed sample answers matched their expected marks and points.'
        reviews.save_question(db, principal, paper_id, SaveReviewQuestion(
            number=number, expectedRevision=row.revision, status=row.status, data=data), commit=job_id is None)
    elif job_id is None:
        db.commit()
    return dict(passed=passed, cases=cases)


def job_response(job):
    return dict(id=str(job.id), status=job.status, errorCode=job.error_code, result=job.result_data)


def enqueue(db, principal, paper_id, number, payload):
    from app.models import EvidenceLinkJob
    workspace, row, digest = evidence_links._context(db, paper_id, number, lock=True)
    existing = db.get(EvidenceLinkJob, payload.requestId)
    request_data = dict(number=number, sourceHash=digest, payload=payload.model_dump(mode='json'))
    request_data['requestHash'] = hashlib.sha256(json.dumps(request_data['payload'], sort_keys=True).encode()).hexdigest()
    if existing:
        if existing.paper_id != paper_id or existing.job_kind != 'scoring' or existing.request_data.get('requestHash') != request_data['requestHash'] or existing.request_data['number'] != number:
            raise DomainError('scoring_request_conflict', 'This request ID has already been used.', 409)
        return job_response(existing)
    evidence_links._fresh(row, digest, payload.expectedRevision, digest)
    if db.scalar(select(EvidenceLinkJob.id).where(EvidenceLinkJob.paper_id == paper_id,
                 EvidenceLinkJob.status.in_(['queued', 'processing'])).limit(1)):
        raise DomainError('scoring_job_pending', 'Wait for this paper’s active review job to finish.', 409)
    part = next((p for p in row.review_data['parts'] if p['label']==payload.partLabel), None)
    if not payload.confirmReviewed or not part or part['status'] not in {'approved','ai_approved'} or part['responseType'] != 'text':
        raise DomainError('scoring_review_required', 'Choose an approved text subpart and confirm the reviewed examples.', 409)
    job = EvidenceLinkJob(id=payload.requestId, paper_id=paper_id, created_by=principal.user.id,
        job_kind='scoring', status='queued', request_data=request_data, result_data={})
    db.add(job)
    db.commit()
    return job_response(job)


def get_job(db, paper_id, job_id):
    from app.models import EvidenceLinkJob
    job = db.get(EvidenceLinkJob, job_id)
    if not job or job.paper_id != paper_id or job.job_kind != 'scoring':
        raise DomainError('scoring_job_not_found', 'Scoring validation job not found.', 404)
    return job_response(job)


def process_next(db, settings, *, generator=None):
    from datetime import datetime, timedelta, timezone
    from app.models import EvidenceLinkJob, User
    now = datetime.now(timezone.utc)
    for job in db.scalars(select(EvidenceLinkJob).where(EvidenceLinkJob.job_kind=='scoring',
            EvidenceLinkJob.status=='processing', EvidenceLinkJob.started_at<now-timedelta(hours=1))
            .with_for_update(skip_locked=True)):
        job.status='failed'
        job.error_code='scoring_job_interrupted'
        job.completed_at=now
        job.request_data={**job.request_data,'payload':{}}
    job = db.scalar(select(EvidenceLinkJob).where(EvidenceLinkJob.job_kind=='scoring',
        EvidenceLinkJob.status=='queued').order_by(EvidenceLinkJob.created_at).limit(1).with_for_update(skip_locked=True))
    if not job:
        db.commit()
        return
    job.status='processing'
    job.started_at=now
    jid=job.id
    db.commit()
    try:
        actor=db.get(User,job.created_by)
        if not actor or not actor.is_active or actor.role!='admin':
            raise DomainError('permission_denied','Requesting Admin is inactive.',403)
        result=run(db,settings,SimpleNamespace(user=actor),job.paper_id,job.request_data['number'],
            ValidateScoring.model_validate(job.request_data['payload']), generator=generator,
            expected_source_hash=job.request_data['sourceHash'], job_id=jid)
        job=db.get(EvidenceLinkJob,jid)
        job.status='completed'
        job.result_data=result
    except Exception as exc:
        db.rollback()
        job=db.get(EvidenceLinkJob,jid)
        job.status='failed'
        job.error_code=exc.code if isinstance(exc,DomainError) else 'scoring_invalid_result'
        if isinstance(exc, DomainError) and exc.code == 'assessment_output_invalid':
            job.result_data = {'failureReason': exc.message}
    job.request_data={**job.request_data,'payload':{}}
    job.completed_at=datetime.now(timezone.utc)
    db.commit()
