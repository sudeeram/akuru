"""Source-reviewed corrections via a no-inference unit of work.

No provider/router/AI-job imports. Immutable prepared packages and receipts use
existing indexed AuditEvent storage; transaction ownership stays with callers.
"""
import copy
import hashlib
import json
import uuid
from datetime import datetime,timezone
from sqlalchemy import select,or_,and_
from pydantic import ValidationError
from app.errors import DomainError
from app.models import AuditEvent,OfficialPaperReviewQuestion,OfficialQuestionAnalysis,DocumentAsset
from app.schemas.official_paper_reviews import ReviewQuestionData
from app.schemas.paper_analysis import RecordQuestionAnalysis
from app.schemas.developer_reviews import StageReview,ApplyReview
from . import official_paper_reviews as reviews,official_question_analyses as analyses,review_scopes

STAGED='developer_review.staged'
APPLIED='developer_review.applied'
BATCH='developer_review.batch'

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()

def context(db,paper,number,lock=False):
    w,q=analyses._context(db,paper,number,lock=lock)
    from .evidence_links import _context
    _,_,source_hash=_context(db,paper,number,lock=lock)
    return w,q,source_hash

def audit(db,principal,action,paper,value,event_id=None):
    row=AuditEvent(id=event_id or uuid.uuid4(),actor_id=principal.user.id,action=action,
        target_type='document',target_id=str(paper),event_data=value,created_at=datetime.now(timezone.utc))
    db.add(row);db.flush();return row

def staged(db,paper,key):
    row=db.get(AuditEvent,key)
    if not row or row.action!=STAGED or row.target_id!=str(paper):raise DomainError('review_change_not_found','Prepared change set not found.',404)
    return row

def _fresh(db,w,q,payload):
    from .accuracy_jobs import _version
    if q.revision!=payload.expectedRevision or analyses.content_hash(db,q,analyses.source_manifest(db,w))!=payload.expectedContentHash or _version(db,q)!=payload.expectedAnalysisVersion:
        raise DomainError('review_change_stale','Question, source or analysis changed. Prepare a fresh preview.',409)

def _target(db,w,q,payload,base_scopes=None):
    if base_scopes is None:_fresh(db,w,q,payload)
    before=ReviewQuestionData.model_validate(q.review_data);data=ReviewQuestionData.model_validate(before.model_dump(mode='json')|payload.sharedFields)
    base_scopes=base_scopes or review_scopes.bindings(db,w,q)
    changes=[]
    for correction in payload.corrections:
        part=next((p for p in data.parts if p.label==correction.partLabel),None)
        if not part or base_scopes.get(part.label)!=correction.expectedScopeHash:
            raise DomainError('review_scope_stale','Subpart identity or reviewed scope changed.',409)
        supplied=part.model_dump(mode='json')|correction.fields
        updated=type(part).model_validate(supplied)
        old_certificate=part.scoringRules.deterministic.certificateId if part.scoringRules.deterministic else None
        new_certificate=updated.scoringRules.deterministic.certificateId if updated.scoringRules.deterministic else None
        if new_certificate is not None and new_certificate!=old_certificate:
            raise DomainError('review_certificate_forbidden','Scoring certificates must come from server validation.',422)
        changed=[k for k in correction.fields if supplied[k]!=part.model_dump(mode='json').get(k)]
        if changed and part.status=='approved' and not payload.reopenApproved:
            raise DomainError('review_reopen_required','Explicitly reopen only the corrected approved subpart.',409)
        if changed and not correction.sourceFinding:
            raise DomainError('review_finding_required','Supply a source comparison for the changed subpart.',409)
        if changed:
            updated.status='unreviewed'
            if updated.scoringRules.deterministic:
                from .deterministic_validation import certificate
                if not certificate(db,w,q,data,updated):
                    updated.scoringRules.deterministic.certificateId=None
                    updated.assessmentReadiness='unreviewed'
                    updated.assessmentReadinessReason='Source content changed; replay affected scoring validation.'
            elif updated.assessmentReadiness=='automatic' and set(changed)&{'prompt','markingPoints','alternatives','scoringRules','paperSources','schemeSources','visualAssetIds'}:
                updated.assessmentReadiness='unreviewed'
                updated.assessmentReadinessReason='Material scoring dependencies changed; validate the revised rubric.'
        data.parts[data.parts.index(part)]=updated
        changes.append(dict(partLabel=part.label,fields=changed,before=part.model_dump(mode='json'),after=updated.model_dump(mode='json')))
    for decision in payload.visualDecisions:
        asset=db.get(DocumentAsset,decision.assetId)
        if not asset or str(asset.document_version_id)!=str(getattr(w,decision.sourceRole+'_version_id'))or asset.sha256!=decision.expectedSha256 or not asset.asset_metadata.get('reviewCrop'):
            raise DomainError('review_visual_changed','Choose a crop from the exact bound source/version.',409)
        if decision.sourceRole=='scheme':
            part=next((p for p in data.parts if p.label==decision.partLabel),None)
            if not part:raise DomainError('review_visual_part','Answer visuals require a specific subpart.',422)
            visual=next((v for v in part.answerVisuals if v.assetId==decision.assetId),None)
            if not visual:raise DomainError('review_visual_reference','Attach the typed official answer-visual reference in the correction.',422)
            visual.status='approved'if decision.decision=='approve'else'rejected';visual.caption=decision.caption;visual.altText=decision.altText
        else:
            data.candidateVisualAssetIds=[v for v in data.candidateVisualAssetIds if v!=decision.assetId]
            if decision.partLabel is None:placements=data.visualAssetIds
            else:
                part=next((p for p in data.parts if p.label==decision.partLabel),None)
                if not part:raise DomainError('review_visual_part','Choose an existing subpart.',422)
                placements=part.visualAssetIds
            if decision.decision=='approve'and decision.assetId not in placements:placements.append(decision.assetId)
            if decision.decision=='reject'and decision.assetId in placements:placements.remove(decision.assetId)
    # Source changes through shared context or a visual also affect dependencies.
    prospective=type('Prospective',(),dict(review_data=data.model_dump(mode='json')))()
    selected={c.partLabel:c for c in payload.corrections}
    for part in data.parts:
        affected=base_scopes[part.label]!=review_scopes.binding(db,w,prospective,part.label)
        if affected:
            correction=selected.get(part.label)
            if not correction or not correction.sourceFinding:raise DomainError('review_finding_required','Every affected shared/visual scope needs a source comparison.',409)
            prior=next(p for p in before.parts if p.label==part.label)
            if prior.status=='approved'and not payload.reopenApproved:raise DomainError('review_reopen_required','Explicitly reopen affected human-reviewed content.',409)
            part.status='unreviewed'
            if part.scoringRules.deterministic:
                from .deterministic_validation import certificate
                if not certificate(db,w,q,data,part):
                    part.scoringRules.deterministic.certificateId=None;part.assessmentReadiness='unreviewed'
        existing=next(c for c in changes if c['partLabel']==part.label)if part.label in selected else None
        if existing:
            fields=[key for key in type(part).model_fields if key not in {'status','assessmentReadiness','assessmentReadinessReason'}and existing['before'].get(key)!=part.model_dump(mode='json').get(key)]
            existing.update(after=part.model_dump(mode='json'),fields=fields or (['visualMetadata']if affected else []))
    if before.sharedStem!=data.sharedStem or any('prompt'in change['fields']for change in changes):
        if not data.sharedStem and 'sharedStem'not in payload.sharedFields:
            raise DomainError('review_shared_context_required','Confirm the shared stem explicitly before rebuilding aggregate question wording.',409)
        data.prompt='\n\n'.join(value for value in [data.sharedStem,*[f'({part.label}) {part.prompt}'for part in data.parts]]if value)
        data=ReviewQuestionData.model_validate(data.model_dump(mode='json'))
    return before,data,changes


def target(db,w,q,payload,base_scopes=None):
    try:
        return _target(db,w,q,payload,base_scopes)
    except ValidationError as exc:
        raise DomainError('review_content_invalid','Correction fields do not match the question content schema.',422) from exc


def visual_metadata(db,w,payload):
    for decision in sorted(payload.visualDecisions,key=lambda d:str(d.assetId)):
        asset=db.scalar(select(DocumentAsset).where(DocumentAsset.id==decision.assetId).with_for_update())
        if not asset or str(asset.document_version_id)!=str(getattr(w,decision.sourceRole+'_version_id'))or asset.sha256!=decision.expectedSha256:
            raise DomainError('review_visual_changed','The reviewed visual changed.',409)
        asset.asset_metadata={**asset.asset_metadata,'reviewApproved':decision.decision=='approve','caption':decision.caption,'altText':decision.altText}
    db.flush()

def stage(db,principal,paper,payload):
    body=payload.model_dump(mode='json');existing=db.get(AuditEvent,payload.requestId)
    if existing:
        if existing.action!=STAGED or existing.target_id!=str(paper)or existing.actor_id!=principal.user.id or existing.event_data.get('payload')!=body:
            raise DomainError('review_request_conflict','Request ID already used for another operation.',409)
        return change_set(db,paper,existing.id)
    w,q,_=context(db,paper,payload.number)
    _,_,changes=target(db,w,q,payload)
    audit(db,principal,STAGED,paper,dict(payload=body,requestHash=digest(body),changes=changes),payload.requestId)
    db.commit();return change_set(db,paper,payload.requestId)

def change_set(db,paper,key):
    row=staged(db,paper,key)
    receipt=db.scalar(select(AuditEvent).where(AuditEvent.action==APPLIED,AuditEvent.target_id==str(paper),AuditEvent.event_data['changeSetId'].as_string()==str(key)))
    return dict(id=str(row.id),createdAt=row.created_at,payload=row.event_data['payload'],state='applied'if receipt else'prepared',receipt=receipt.event_data if receipt else None,current=(all(review_scopes.binding(db,*analyses._context(db,paper,receipt.event_data['number']),label)==value for label,value in receipt.event_data.get('scopeBindings',{}).items())if receipt else None),noInference=True)

def _preview(db,paper,key,base_scopes=None):
    row=staged(db,paper,key);payload=StageReview.model_validate(row.event_data['payload'])
    w,q,_=context(db,paper,payload.number)
    before,data,changes=target(db,w,q,payload,base_scopes)
    # Validate reference ownership and all normal content contracts before writing.
    reviews._validate_question(db,w,'unreviewed',data,q.review_data,q.number)
    selected={c.partLabel for c in payload.corrections}
    from .tutor_past_papers import topic_publications
    from .paper_curriculum import mapping_hash
    publication_bindings=[]
    for part in data.parts:
        try:publications=topic_publications(db,w,part)if part.topicRefs else []
        except DomainError as exc:publications=[dict(blocker=exc.code)]
        publication_bindings.append(dict(partLabel=part.label,mappingHash=mapping_hash(part.model_dump(mode='json')),publications=publications))
    value=dict(changeSetId=str(key),number=q.number,baseRevision=q.revision,baseContentHash=payload.expectedContentHash,
        changes=changes,carriedForwardParts=[p.label for p in data.parts if p.label not in selected],
        affectedParts=sorted(selected),sourceVersions=analyses.source_manifest(db,w),
        assembledPrompt=dict(before=before.prompt,after=data.prompt)if before.prompt!=data.prompt else None,publicationBindings=publication_bindings,sharedFields=payload.sharedFields,visualDecisions=[v.model_dump(mode='json')for v in payload.visualDecisions],issueDecisions=[v.model_dump(mode='json')for v in payload.issueDecisions],gateImpact=[dict(partLabel=c['partLabel'],sourceRecheckRequired=bool(c['fields']),scoringBefore=c['before']['assessmentReadiness'],scoringAfter=c['after']['assessmentReadiness'],releaseDependenciesChanged=bool(c['fields'])) for c in changes],noInference=True,formalPublication=False)
    value['previewHash']=digest(value)
    return value

def preview(db,paper,key):
    row=staged(db,paper,key);payload=StageReview.model_validate(row.event_data['payload'])
    if not payload.visualDecisions:return _preview(db,paper,key)
    w,q,_=context(db,paper,payload.number);_fresh(db,w,q,payload);base=review_scopes.bindings(db,w,q)
    transaction=db.begin_nested()
    try:
        visual_metadata(db,w,payload)
        return _preview(db,paper,key,base)
    finally:transaction.rollback()


def _analysis_payload(db,w,q,old,payload,previous_data,previous_bindings,baseline_current):
    if not old:raise DomainError('review_baseline_required','Record a complete baseline source comparison before a scoped correction.',409)
    prior={p['label']:p for p in old.analysis_data['parts']};selected={c.partLabel:c for c in payload.corrections};parts=[];origins={}
    previous=type('Previous',(),dict(review_data=previous_data))()
    for p in q.review_data['parts']:
        label=p['label'];c=selected.get(label)
        if c and c.sourceFinding:
            parts.append(c.sourceFinding.model_dump(mode='json'));origins[label]=dict(kind='new_comparison')
        else:
            certified=old.analysis_data.get('_scopeBindings',{}).get(label) or (previous_bindings[label]if baseline_current else None)
            if label not in prior or certified!=review_scopes.binding(db,w,q,label):
                raise DomainError('review_carry_invalid','Unchanged source evidence cannot be established; supply a new comparison.',409)
            parts.append(copy.deepcopy(prior[label]));origins[label]=dict(kind='carried_forward',analysisId=str(old.id))
    question=payload.questionFinding.model_dump(mode='json')if payload.questionFinding else copy.deepcopy(old.analysis_data['question'])
    question['percent']=min(question['percent'],*(part['percent']for part in parts))
    from .accuracy_jobs import _version
    analysis=RecordQuestionAnalysis(expectedQuestionRevision=q.revision,expectedAnalysisVersion=_version(db,q),
        expectedContentHash=analyses.content_hash(db,q,analyses.source_manifest(db,w)),stage='accuracy',
        methodVersion=old.analysis_data['methodVersion'],provenance=payload.provenance,question=question,parts=parts)
    return analysis,origins

def _apply(db,principal,paper,key,request,*,commit=True):
    entry=staged(db,paper,key);payload=StageReview.model_validate(entry.event_data['payload'])
    w,q,_=context(db,paper,payload.number,lock=True)
    prior=db.scalar(select(AuditEvent).where(AuditEvent.action==APPLIED,AuditEvent.target_id==str(paper),AuditEvent.event_data['changeSetId'].as_string()==str(key)))
    if prior:
        if prior.event_data['applyRequestHash']!=digest(request.model_dump(mode='json')):raise DomainError('review_request_conflict','Applied change set differs from this request.',409)
        return prior.event_data
    if db.get(AuditEvent,request.requestId):raise DomainError('review_request_conflict','Request ID already used.',409)
    view=preview(db,paper,key)
    if view['previewHash']!=request.expectedPreviewHash:raise DomainError('review_preview_changed','Review the exact current preview before applying.',409)
    from .question_auto_approval import current_accuracy
    old=current_accuracy(db,w,q)
    baseline_current=old is not None
    if old is None:
        old=db.scalar(select(OfficialQuestionAnalysis).where(OfficialQuestionAnalysis.question_id==q.id,OfficialQuestionAnalysis.stage=='accuracy').order_by(OfficialQuestionAnalysis.version_number.desc()).limit(1))
    base_scopes=review_scopes.bindings(db,w,q)
    visual_metadata(db,w,payload)
    before,data,changes=target(db,w,q,payload,base_scopes)
    if not old:raise DomainError('review_baseline_required','Record a complete baseline source inventory before scoped correction.',409)
    from . import paper_source_issues
    old_decisions=paper_source_issues.decisions(db,[q.id])
    old_issues=[(None,i)for i in old.analysis_data['question'].get('issues',[])]+[(p['label'],i)for p in old.analysis_data['parts']for i in p.get('issues',[])]
    changed={c['partLabel']for c in changes if c['fields']}
    # Only the selected changed part is reopened. Human sibling decisions survive.
    q.review_data=data.model_dump(mode='json');q.revision+=1
    if changed:q.status='unreviewed'
    db.flush()
    assembled,origins=_analysis_payload(db,w,q,old,payload,before.model_dump(mode='json'),base_scopes,baseline_current)
    recorded=analyses.record(db,principal,paper,q.number,assembled,commit=False,evaluate_approval=False)
    new=db.get(type(old),uuid.UUID(recorded.id));new.analysis_data={**new.analysis_data,'_reviewOrigins':origins}
    for label,issue in old_issues:
        if label is not None and label not in changed and paper_source_issues.is_resolved(issue,old,label,old_decisions):
            db.add(AuditEvent(actor_id=principal.user.id,action='official_review.source_issue_resolved',target_type='official_paper_review_question',target_id=str(q.id),
                event_data=dict(issueId=issue['id'],partLabel=label,contentHash=new.content_hash,analysisId=str(new.id),
                    scopeBinding=new.analysis_data.get('_scopeBindings',{}).get(label),disposition=next((e.event_data.get('disposition') for e in reversed(old_decisions) if e.event_data.get('issueId')==issue['id'] and e.event_data.get('partLabel')==label and paper_source_issues.is_resolved(issue,old,label,[e])),None),origin='carried_forward',priorAnalysisId=str(old.id),note='Unchanged source decision carried forward with its original evidence.')))
    for decision in payload.issueDecisions:
        issue=next((i for label,i in old_issues if label==decision.partLabel and i['id']==decision.issueId),None)
        if not issue:raise DomainError('review_issue_changed','Issue is not in the reviewed baseline.',409)
        if decision.disposition=='still_unresolved':continue
        if issue['kind']=='extraction' and decision.disposition!='corrected_and_rechecked':
            raise DomainError('review_issue_not_corrected','Extraction omissions need an actual source correction, not a discrepancy override.',409)
        if decision.disposition=='corrected_and_rechecked':
            relevant={'paper':{'prompt','paperSources','visualAssetIds','visualMetadata'},'scheme':{'markingPoints','alternatives','scoringRules','schemeSources','answerVisuals'},'report':{'examinerAdvice','reportSources'}}[issue['role']]
            actual=next((set(c['fields']) for c in changes if c['partLabel']==decision.partLabel),set())
            if not actual&relevant:raise DomainError('review_issue_not_corrected','Correct the content fields relevant to this source issue.',409)
        if decision.disposition=='corrected_and_rechecked' and (decision.partLabel not in changed or not next(c.sourceFinding for c in payload.corrections if c.partLabel==decision.partLabel)):
            raise DomainError('review_issue_not_corrected','Extraction resolution requires a correction and source recheck.',409)
        db.add(AuditEvent(actor_id=principal.user.id,action='official_review.source_issue_resolved',target_type='official_paper_review_question',target_id=str(q.id),
            event_data=dict(issueId=issue['id'],partLabel=decision.partLabel,contentHash=new.content_hash,analysisId=str(new.id),
                scopeBinding=new.analysis_data.get('_scopeBindings',{}).get(decision.partLabel),disposition=decision.disposition,note=decision.note,changeSetId=str(key))))
    db.flush()
    approval=None
    if request.evaluateApproval:
        from .question_auto_approval import apply as evaluate
        approval=evaluate(db,principal,w,q,labels={c.partLabel for c in payload.corrections})
    releases=[]
    if request.releaseTutor:
        from .tutor_past_papers import auto_release
        releases=auto_release(db,principal,w,q)
    result=dict(changeSetId=str(key),number=q.number,revision=q.revision,analysisId=recorded.id,analysisVersion=recorded.version,
        scopeBindings={c.partLabel:review_scopes.binding(db,w,q,c.partLabel)for c in payload.corrections},origins=origins,approval=approval,tutorReleases=releases,noInference=True,modelInvocations=0,formalPublication=False,
        applyRequestHash=digest(request.model_dump(mode='json')))
    audit(db,principal,APPLIED,paper,result,request.requestId)
    if commit:db.commit()
    return result

def apply(db,principal,paper,key,request,*,commit=True):
    # Roll back the complete correction even when an API/test caller reuses its
    # Session after a handled domain error. Never rely on connection close.
    try:
        with db.begin_nested():
            result=_apply(db,principal,paper,key,request,commit=False)
    except ValidationError as exc:
        raise DomainError('review_analysis_invalid','Prepared findings must use the baseline assessment policy and valid source contracts.',422) from exc
    if commit:db.commit()
    else:db.flush()
    return result


def history(db,paper,limit=50,offset=0):
    w=reviews._workspace(db,paper)
    ids=[str(value)for value in db.scalars(select(OfficialPaperReviewQuestion.id).where(OfficialPaperReviewQuestion.workspace_id==w.id))]
    relevant=or_(and_(AuditEvent.target_id==str(paper),or_(AuditEvent.action.like('developer_review.%'),AuditEvent.action.like('official_review.%'))),and_(AuditEvent.target_id.in_(ids),or_(AuditEvent.action.like('official_review.%'),AuditEvent.action.like('tutor_paper.%'))))
    return [dict(id=str(r.id),actorId=str(r.actor_id)if r.actor_id else None,action=r.action,createdAt=r.created_at,targetId=r.target_id,data=r.event_data)for r in db.scalars(select(AuditEvent).where(relevant).order_by(AuditEvent.created_at.desc(),AuditEvent.id.desc()).offset(offset).limit(limit))]


def readiness(db,paper,numbers=None):
    w=reviews._workspace(db,paper);review=reviews.get(db,paper)
    from . import tutor_past_papers,deterministic_validation,paper_source_issues
    rows=[]
    for q in db.scalars(select(OfficialPaperReviewQuestion).where(OfficialPaperReviewQuestion.workspace_id==w.id).order_by(OfficialPaperReviewQuestion.number)):
        if numbers and q.number not in numbers:continue
        data=ReviewQuestionData.model_validate(q.review_data)
        for part in data.parts:
            analysis=review_scopes.current_analysis(db,w,q,part.label)
            estimate=next((p for p in analysis.analysis_data['parts']if p['label']==part.label),None)if analysis else None
            blockers=[]
            if not analysis:blockers.append(dict(code='source_assessment_stale',gate='sourceAccuracy',action='record_source_assessment'))
            if estimate and estimate['percent']<=75:blockers.append(dict(code='confidence_below_threshold',gate='contentApproval',action='compare_original_sources'))
            issues=paper_source_issues.blocking(analysis,part.label,paper_source_issues.decisions(db,[q.id]))
            blockers.extend(dict(code='source_'+i['kind'],gate='sourceIssues',issueId=i['id'],action='correct_or_adjudicate_source')for i in issues)
            for blocker in blockers:blocker.update(severity='blocking',needsSourceInterpretation=blocker['gate']in {'sourceAccuracy','sourceIssues'},usesModel=False)
            report_check=next((s for s in (estimate or {}).get('sourceChecks',[])if s['role']=='report'),None)
            certificate=deterministic_validation.certificate(db,w,q,data,part)if part.scoringRules.deterministic else None
            try:tutor_past_papers.validate_release(db,w,q,part.label);tutor=True
            except DomainError as exc:
                tutor=False;blockers.append(dict(code=exc.code,gate='tutorRelease',message=exc.message,action='inspect_release_gate',severity='blocking',needsSourceInterpretation=False,usesModel=False))
            rows.append(dict(number=q.number,partLabel=part.label,partRef=review_scopes.part_ref(q,part.label),scopeHash=review_scopes.binding(db,w,q,part.label),
                revision=q.revision,contentApproval=part.status,sourceAccuracy=dict(current=analysis is not None,percent=estimate['percent']if estimate else None,origin=analysis.analysis_data.get('_reviewOrigins',{}).get(part.label,{}).get('kind','original_comparison')if analysis else None),
                curriculum=dict(coverage=part.coverage,topicRefs=part.topicRefs),scoringReadiness=dict(status=part.assessmentReadiness,reason=part.assessmentReadinessReason,certificateId=str(certificate.id)if certificate else None),
                reportGuidance=dict(status=report_check['status']if report_check else 'not_checked',usable=bool(analysis and paper_source_issues.report_usable(analysis,part.label,paper_source_issues.decisions(db,[q.id])))),evidence=dict(paper=[r.model_dump(mode='json')for r in part.paperSources],scheme=[r.model_dump(mode='json')for r in part.schemeSources],report=[r.model_dump(mode='json')for r in part.reportSources]),warnings=([dict(code='report_guidance_withheld',severity='warning',usesModel=False)]if analysis and not paper_source_issues.report_usable(analysis,part.label,paper_source_issues.decisions(db,[q.id]))else []),tutorRelease=dict(eligible=tutor),formalRelease=dict(wholePaperReady=review.wholePaperReady,automaticAssessmentReady=review.automaticAssessmentReady),tutorEligible=tutor,blockers=blockers))
    return dict(paperId=str(paper),parts=rows,wholePaperReady=review.wholePaperReady,automaticAssessmentReady=review.automaticAssessmentReady,
        blockers=review.blockers,noInference=True)


def export_package(db,paper,numbers=None,offset=0,limit=10):
    from . import paper_source_issues
    w=reviews._workspace(db,paper);review=reviews.get(db,paper)
    selected=[q for q in review.questions if not numbers or q.number in numbers]
    rowmap={q.number:q for q in db.scalars(select(OfficialPaperReviewQuestion).where(OfficialPaperReviewQuestion.workspace_id==w.id))}
    result=[]
    for q in selected[offset:offset+limit]:
        row=rowmap[q.number]
        result.append(dict(question=q.model_dump(mode='json'),scopes=review_scopes.bindings(db,w,row),
            partRefs={p.label:review_scopes.part_ref(row,p.label)for p in q.data.parts},
            sourceIssues=paper_source_issues.listing(db,paper,q.number)))
    return dict(schema=1,paperId=str(paper),sources=analyses.source_manifest(db,w),questions=result,offset=offset,limit=limit,total=len(selected),
        originalDocuments=[dict(role=role,documentId=str(getattr(w,role+'_document_id')),url=f'/api/v1/documents/{getattr(w,role+"_document_id")}/content')for role in ['paper','scheme','report']if getattr(w,role+'_document_id')],
        noInference=True)


def approve(db,principal,paper,number,payload):
    w,q,_=context(db,paper,number,lock=True)
    existing=db.get(AuditEvent,payload.requestId)
    if existing and not payload.dryRun:
        if existing.action!='developer_review.approval' or existing.target_id!=str(paper) or existing.actor_id!=principal.user.id or existing.event_data.get('number')!=number or existing.event_data.get('requestHash')!=digest(payload.model_dump(mode='json')):raise DomainError('review_request_conflict','Request ID already used.',409)
        return existing.event_data
    if q.revision!=payload.expectedRevision:raise DomainError('review_conflict','Reload the current revision.',409)
    known={p['label']for p in q.review_data['parts']}
    if not set(payload.partLabels)<=known:raise DomainError('review_part_not_found','Unknown subpart.',404)
    from .question_auto_approval import apply as evaluate
    if payload.dryRun:
        transaction=db.begin_nested()
        try:result=evaluate(db,principal,w,q,labels=set(payload.partLabels)or None);db.flush()
        finally:transaction.rollback()
        return result|dict(dryRun=True,noInference=True)
    existing=db.get(AuditEvent,payload.requestId)
    if existing:
        if existing.action!='developer_review.approval' or existing.target_id!=str(paper)or existing.event_data.get('requestHash')!=digest(payload.model_dump(mode='json')):raise DomainError('review_request_conflict','Request ID already used.',409)
        return existing.event_data
    result=evaluate(db,principal,w,q,labels=set(payload.partLabels)or None)|dict(number=number,noInference=True,requestHash=digest(payload.model_dump(mode='json')))
    audit(db,principal,'developer_review.approval',paper,result,payload.requestId);db.commit();return result


def validate_release(db,paper,payload):
    state=readiness(db,paper,payload.numbers)
    if payload.target=='tutor_practice':blockers=[dict(number=p['number'],partLabel=p['partLabel'],blockers=p['blockers'])for p in state['parts']if not p['tutorEligible']]
    else:
        review=reviews.get(db,paper)
        blockers=list(state['blockers'])+list(review.assessmentBlockers)
        if not review.assessmentReleaseReady and not blockers:blockers.append('Complete-paper scoring readiness is not satisfied.')
    if payload.target=='formal_exam':
        from types import SimpleNamespace
        from .official_materials import publish_review
        w=reviews._workspace(db,paper)
        confirmation=SimpleNamespace(confirmCourse=True,confirmSubject=True,confirmComplete=True,confirmSourcePaper=True)
        for role,document_id in [('paper',w.paper_document_id),('scheme',w.scheme_document_id)]:
            if not document_id:
                blockers.append(dict(role=role,code='official_source_missing'));continue
            transaction=db.begin_nested()
            try:publish_review(db,None,document_id,confirmation,validate_only=True)
            except DomainError as exc:blockers.append(dict(role=role,code=exc.code,message=exc.message))
            finally:transaction.rollback()
    content=dict(target=payload.target,readiness=state,blockers=blockers,passed=not blockers,noInference=True,published=False)
    from datetime import timedelta
    content['validUntil']=(datetime.now(timezone.utc)+timedelta(minutes=10)).isoformat()
    content['readinessHash']=digest(content)
    return content


def batch_status(db,paper,key):
    row=db.get(AuditEvent,key)
    if not row or row.action!=BATCH or row.target_id!=str(paper):raise DomainError('review_batch_not_found','Review batch not found.',404)
    items=[change_set(db,paper,uuid.UUID(k))for k in row.event_data['payload']['items']]
    return dict(id=str(key),items=items,completed=sum(i['state']=='applied'for i in items),total=len(items),noInference=True)


def run_batch(db,principal,paper,payload,resume=False):
    body=payload.model_dump(mode='json');existing=db.get(AuditEvent,payload.requestId)
    if existing:
        if existing.action!=BATCH or existing.target_id!=str(paper)or existing.actor_id!=principal.user.id or existing.event_data.get('payload')!=body:raise DomainError('review_request_conflict','Batch request ID already used.',409)
    else:
        for key in payload.items:staged(db,paper,key)
        audit(db,principal,BATCH,paper,dict(payload=body),payload.requestId);db.commit()
    results=[]
    for key in payload.items:
        current=change_set(db,paper,key)
        if current['state']=='applied':
            results.append(dict(id=str(key),state='applied'if current['current']else'stale',resumed=True))
            if not current['current']and payload.stopOnConflict:break
            continue
        try:
            if str(key)not in payload.previewHashes:raise DomainError('review_preview_required','Each item needs its reviewed preview hash.',422)
            result=apply(db,principal,paper,key,ApplyReview(requestId=uuid.uuid5(payload.requestId,str(key)),expectedPreviewHash=payload.previewHashes[str(key)],evaluateApproval=payload.evaluateApproval,releaseTutor=payload.releaseTutor))
            results.append(dict(id=str(key),state='applied',receipt=result))
        except DomainError as exc:
            db.rollback();results.append(dict(id=str(key),state='blocked',code=exc.code,message=exc.message))
            if payload.stopOnConflict:break
    audit(db,principal,'developer_review.batch_attempt',paper,dict(batchId=str(payload.requestId),results=results,noInference=True));db.commit()
    return batch_status(db,paper,payload.requestId)|dict(attempt=results)
