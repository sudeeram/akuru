"""Source discrepancies are explicit audited release gates, never confidence caps."""
import hashlib
import json
from datetime import datetime, timezone

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.models import AuditEvent
from app.errors import DomainError


class ResolveSourceIssue(BaseModel):
    analysisId: str = Field(min_length=36, max_length=36)
    issueId: str = Field(pattern=r"^[a-f0-9]{64}$")
    partLabel: str | None = Field(default=None, max_length=40)
    note: str = Field(min_length=10, max_length=2000)


def identify(issue):
    value = {k: issue[k] for k in ('kind', 'role', 'pages', 'description')}
    if value['kind'] == 'extraction' and value['role'] == 'report':
        value['kind'] = 'report_guidance'
    value['pages'] = sorted(set(value['pages']))
    return {**value, 'id': hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()}


def decisions(db, question_ids):
    return list(db.scalars(select(AuditEvent).where(
        AuditEvent.action == 'official_review.source_issue_resolved',
        AuditEvent.target_id.in_([str(v) for v in question_ids]))))


def is_resolved(issue, analysis, label, events):
    return any(e.target_id == str(analysis.question_id)
               and e.event_data.get('issueId') == issue['id']
               and e.event_data.get('partLabel') == label
               and e.event_data.get('contentHash') == analysis.content_hash for e in events)


def blocking(analysis, label, events):
    if not analysis or analysis.analysis_data.get('question', {}).get('confidencePolicy') != 'extraction-v1':
        return []
    scopes = [(None, analysis.analysis_data['question'])]
    if label is not None:
        scopes.extend((p['label'], p) for p in analysis.analysis_data['parts'] if p['label'] == label)
    return [issue for scope_label, scope in scopes for issue in scope.get('issues', [])
            if issue['kind'] in {'source_discrepancy', 'extraction'}
            and not is_resolved(issue, analysis, scope_label, events)]


def report_usable(analysis, label, events):
    if not analysis or analysis.analysis_data.get('question', {}).get('confidencePolicy') != 'extraction-v1':
        return True  # Preserve the historical policy for existing releases.
    part = next((p for p in analysis.analysis_data['parts'] if p['label'] == label), None)
    if not part:
        return False
    source = next((s for s in part['sourceChecks'] if s['role'] == 'report'), None)
    return bool(source and source['status'] == 'checked' and source.get('percent', 0) > 75
                and all(is_resolved(i, analysis, scope_label, events)
                        for scope_label, scope in [(None, analysis.analysis_data['question']), (label, part)]
                        for i in scope.get('issues', []) if i['role'] == 'report'))


def resolve(db, principal, paper_id, number, payload):
    from . import evidence_links, question_auto_approval
    workspace, question, digest = evidence_links._context(db, paper_id, number, lock=True)
    analysis = question_auto_approval.current_accuracy(db, workspace, question)
    if not analysis or str(analysis.id) != payload.analysisId:
        raise DomainError('source_issue_stale', 'Reload the current assessment before resolving this issue.', 409)
    scope = analysis.analysis_data['question'] if payload.partLabel is None else next(
        (p for p in analysis.analysis_data['parts'] if p['label'] == payload.partLabel), {})
    issue = next((i for i in scope.get('issues', []) if i['id'] == payload.issueId), None)
    if not issue or len(payload.note.strip()) < 10:
        raise DomainError('source_issue_required', 'Choose a current issue and record the source-based decision.', 422)
    if not is_resolved(issue, analysis, payload.partLabel, decisions(db, [question.id])):
        db.add(AuditEvent(actor_id=principal.user.id, action='official_review.source_issue_resolved',
            target_type='official_paper_review_question', target_id=str(question.id),
            created_at=datetime.now(timezone.utc), event_data=dict(
                issueId=issue['id'], partLabel=payload.partLabel, contentHash=digest,
                analysisId=str(analysis.id), note=payload.note.strip())))
        db.flush()
    # Resolving an issue is not blanket content approval or a Student-release action.
    db.commit()
    return {'resolved': True}


def listing(db, paper_id, number):
    from . import evidence_links, question_auto_approval
    workspace, question, _ = evidence_links._context(db, paper_id, number)
    analysis = question_auto_approval.current_accuracy(db, workspace, question)
    if not analysis:
        return {'analysisId': None, 'issues': []}
    events = decisions(db, [question.id])
    return {'analysisId': str(analysis.id), 'issues': [
        dict(**issue, partLabel=label, resolved=is_resolved(issue, analysis, label, events),
             resolutionNotes=[e.event_data['note'] for e in events
                if e.event_data.get('issueId') == issue['id']
                and e.event_data.get('partLabel') == label
                and e.event_data.get('contentHash') == analysis.content_hash])
        for label, scope in [(None, analysis.analysis_data['question']),
                             *((p['label'], p) for p in analysis.analysis_data['parts'])]
        for issue in scope.get('issues', [])]}
