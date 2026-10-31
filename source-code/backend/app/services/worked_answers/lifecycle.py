"""Admin draft lifecycle. Generation never edits or approves the question itself."""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from app.errors import DomainError
from app.models import GeneratedWorkedAnswer, OfficialPaperReviewQuestion, DocumentVersion, DocumentBlock, AuditEvent
from app.services.official_paper_reviews import _workspace, _validate_bound_versions, _validate_evidence
from app.schemas.worked_answers import GraphSolution
from .graphs import validate_source, LABEL


def fingerprint(db, workspace, question):
    parts=[]
    for p in question.review_data.get('parts',[]):
        parts.append({k:p.get(k) for k in ('label','prompt','marks','markingPoints','schemeSources','paperSources','reportSources','examinerAdvice','scoringRules')})
    manifest={'questionId':str(question.id),'number':question.number,
              'prompt':question.review_data.get('prompt'), 'sharedStem':question.review_data.get('sharedStem'),
              'parts':parts,'versions':[]}
    for role,vid in (("paper",workspace.paper_version_id),("scheme",workspace.scheme_version_id),("report",workspace.report_version_id)):
        if vid:
            v=db.get(DocumentVersion,vid)
            manifest['versions'].append({'role':role,'id':str(vid),'sha256':v.sha256,'version':v.version_number,'filename':v.original_filename})
    block_ids={source.get('blockId') for part in manifest['parts'] for key in ('schemeSources','paperSources','reportSources') for source in (part.get(key) or []) if source.get('blockId')}
    manifest['evidenceHashes']={}
    for block_id in sorted(block_ids):
        block=db.get(DocumentBlock,uuid.UUID(block_id))
        manifest['evidenceHashes'][block_id]=hashlib.sha256(json.dumps({'text':block.text,'kind':block.block_kind,'version':str(block.document_version_id)},sort_keys=True).encode()).hexdigest() if block else 'missing'
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return digest,manifest


def context(db,paper_id,number, *, lock=True):
    workspace=_workspace(db,paper_id)
    _validate_bound_versions(db,workspace)
    query=select(OfficialPaperReviewQuestion).where(
        OfficialPaperReviewQuestion.workspace_id==workspace.id,OfficialPaperReviewQuestion.number==number)
    question=db.scalar(query.with_for_update() if lock else query)
    if not question: raise DomainError('question_not_found','Save the question review first.',404)
    if not workspace.scheme_version_id: raise DomainError('scheme_required','Attach the exact marking scheme first.',409)
    return workspace,question


def response(row,current_hash):
    return dict(id=str(row.id),questionId=str(row.question_id),revision=row.revision,
                status='stale' if current_hash!=row.source_hash else row.status,
                sourceHash=row.source_hash,sourceManifest=row.source_manifest,graphInput=row.graph_input,
                solution=row.solution,provenance=row.provenance,assets=row.assets,errorCode=row.error_code,
                label=LABEL,createdAt=row.created_at,reviewedAt=row.reviewed_at)


def listing(db,paper_id,number):
    w,q=context(db,paper_id,number,lock=False); digest,_=fingerprint(db,w,q)
    return [response(r,digest) for r in db.scalars(select(GeneratedWorkedAnswer).where(
        GeneratedWorkedAnswer.question_id==q.id).order_by(GeneratedWorkedAnswer.created_at.desc()))]


def audit(db,actor,row,action,note=''):
    db.add(AuditEvent(actor_id=actor,action='worked_answer.'+action,target_type='worked_answer',target_id=str(row.id),
        event_data={'revision':row.revision,'sourceHash':row.source_hash,'note':note}))


def create(db,principal,paper_id,number,payload):
    w,q=context(db,paper_id,number)
    if q.revision!=payload.expectedQuestionRevision:
        raise DomainError('review_conflict','Question changed. Reload before generating.',409)
    parts={p['label']:p for p in q.review_data.get('parts',[])}
    for label in payload.graph.partLabels:
        part=parts.get(label)
        if not part or not part.get('markingPoints') or not part.get('schemeSources'):
            raise DomainError('worked_source_incomplete','Select subparts with reviewed wording and exact marking evidence.',409)
    from app.schemas.official_paper_reviews import ReviewQuestionData
    selected_parts=ReviewQuestionData.model_validate(q.review_data).parts
    for part in selected_parts:
        if part.label in payload.graph.partLabels:
            _validate_evidence(db,w.paper_version_id,part.paperSources,'paper')
            _validate_evidence(db,w.scheme_version_id,part.schemeSources,'scheme')
            if not any(s.blockId for s in part.paperSources) or not any(s.blockId for s in part.schemeSources):
                raise DomainError('worked_source_incomplete','Link exact paper and scheme evidence for each selected part before generation.',409)
    digest,manifest=fingerprint(db,w,q)
    if len(json.dumps(manifest)) > 60000:
        raise DomainError('worked_source_too_large','This question exceeds the bounded generation context. Split the review before generating.',422)
    existing=db.scalars(select(GeneratedWorkedAnswer).where(GeneratedWorkedAnswer.question_id==q.id).order_by(GeneratedWorkedAnswer.created_at.desc())).all()
    if any(r.status in ('queued','processing') for r in existing):
        raise DomainError('generation_running','This question already has a pending generation.',409)
    for r in existing:
        if r.source_hash==digest and r.graph_input==payload.graph.model_dump() and r.status in ('awaiting_review','approved') and not payload.regenerate:
            return response(r,digest)
    row=GeneratedWorkedAnswer(id=uuid.uuid4(),question_id=q.id,source_hash=digest,source_manifest=manifest,
        graph_input=payload.graph.model_dump(),created_by=principal.user.id,status='queued',revision=1,
        provenance={'sourceQuestionRevision':q.revision})
    db.add(row);audit(db,principal.user.id,row,'queued',payload.graph.verificationNote)
    db.commit();db.refresh(row)
    return response(row,digest)


def review(db,principal,paper_id,number,answer_id,payload):
    w,q=context(db,paper_id,number)
    row=db.scalar(select(GeneratedWorkedAnswer).where(GeneratedWorkedAnswer.id==answer_id,
        GeneratedWorkedAnswer.question_id==q.id).with_for_update())
    if not row: raise DomainError('worked_answer_not_found','Worked answer not found.',404)
    digest,_=fingerprint(db,w,q)
    if row.revision!=payload.expectedRevision: raise DomainError('review_conflict','Worked answer changed. Reload before saving.',409)
    if row.source_hash!=digest: raise DomainError('worked_answer_stale','Source changed. Generate a new answer from the current source.',409)
    if row.status not in ('awaiting_review','approved','rejected'):
        raise DomainError('worked_answer_not_ready','Wait for a successful generation before reviewing.',409)
    if payload.action=='edit':
        if not payload.solution: raise DomainError('solution_required','Provide the edited structured solution.',422)
        try:
            validate_source(payload.solution,row.graph_input)
            from .graphs import render
            for i in range(len(payload.solution.steps)): render(payload.solution,i)
        except ValueError as exc:
            raise DomainError('worked_answer_invalid', str(exc), 422) from exc
        row.solution=payload.solution.model_dump();row.assets=[];row.status='awaiting_review'
        row.reviewed_by=None;row.reviewed_at=None
    elif payload.action=='approve':
        if payload.solution is not None: raise DomainError('save_edits_first','Save and preview edits before approving.',422)
        solution=GraphSolution.model_validate(row.solution);validate_source(solution,row.graph_input)
        row.status='approved';row.reviewed_by=principal.user.id;row.reviewed_at=datetime.now(timezone.utc)
    else:
        row.status='rejected';row.reviewed_by=principal.user.id;row.reviewed_at=datetime.now(timezone.utc)
    row.revision+=1
    audit(db,principal.user.id,row,payload.action,payload.reviewNote)
    db.commit();db.refresh(row)
    return response(row,digest)


def attach(db,storage,principal,paper_id,number,answer_id,expected_question_revision):
    """Attach approved immutable PNGs to the ordinary private answer release path."""
    from app.models import DocumentAsset
    from .graphs import render
    w,q=context(db,paper_id,number)
    if q.revision!=expected_question_revision:
        raise DomainError('review_conflict','Reload the question before attaching the answer.',409)
    row=db.scalar(select(GeneratedWorkedAnswer).where(GeneratedWorkedAnswer.id==answer_id,
        GeneratedWorkedAnswer.question_id==q.id).with_for_update())
    digest,_=fingerprint(db,w,q)
    if not row or row.status!='approved' or row.source_hash!=digest:
        raise DomainError('worked_answer_not_approved','Approve a current worked answer before attaching it.',409)
    if q.status=='approved':
        raise DomainError('reopen_required','Reopen the question before attaching a new answer. Existing release snapshots remain unchanged.',409)
    solution=GraphSolution.model_validate(row.solution)
    validate_source(solution,row.graph_input)
    data=json.loads(json.dumps(q.review_data))
    assets=[]
    for i,step in enumerate(solution.steps):
        content=render(solution,i); content_hash=hashlib.sha256(content).hexdigest()
        key=f'generated-answers/{row.id}/{row.revision}/{i}-{content_hash}.png'
        asset=db.scalar(select(DocumentAsset).where(DocumentAsset.object_key==key))
        if not asset:
            storage.put(key,content,'image/png')
            asset=DocumentAsset(id=uuid.uuid4(),document_version_id=w.scheme_version_id,asset_kind='generated_answer',
                object_key=key,mime_type='image/png',sha256=content_hash,size_bytes=len(content),
                asset_metadata={'answerVisual':True,'generatedAnswer':True,'workedAnswerId':str(row.id),
                    'sourceHash':digest,'questionId':str(q.id),'partLabel':step.partLabel,'label':LABEL,
                    'solutionHash':hashlib.sha256(json.dumps(row.solution,sort_keys=True).encode()).hexdigest(),
                    'explanation':step.explanation,'limitations':solution.limitations,
                    'dataText': '; '.join(f'{p.x:g}, {p.y:g}' for p in solution.points),
                    'provenance':row.provenance,'reviewedBy':str(row.reviewed_by),'reviewedAt':row.reviewed_at.isoformat()})
            db.add(asset)
        part=next(p for p in data['parts'] if p['label']==step.partLabel)
        entry={'assetId':str(asset.id),'partLabel':step.partLabel,'pointCodes':[p['code'] for p in part['markingPoints']],
            'caption':solution.title,'altText':f"{solution.xAxis.label}; {solution.yAxis.label}. {step.explanation}"[:2000],
            'status':'approved','origin':'ai_generated','workedAnswerId':str(row.id),
            'explanation':step.explanation,'limitations':solution.limitations,
            'dataText': '; '.join(f'{p.x:g}, {p.y:g}' for p in solution.points)}
        # Replace only previous generated answers for this part, not official crops.
        part['answerVisuals']=[v for v in part.get('answerVisuals',[]) if v.get('origin')!='ai_generated']+[entry]
        assets.append(str(asset.id))
    if data == q.review_data and assets == row.assets:
        return {'questionRevision':q.revision,'assetIds':assets}
    from app.schemas.official_paper_reviews import ReviewQuestionData
    from app.services.official_paper_reviews import _validate_question
    db.flush()
    _validate_question(db,w,q.status,ReviewQuestionData.model_validate(data),q.review_data,q.number)
    referenced={v.get('workedAnswerId') for part in data['parts'] for v in part.get('answerVisuals',[]) if v.get('origin')=='ai_generated'}
    for older in db.scalars(select(GeneratedWorkedAnswer).where(GeneratedWorkedAnswer.question_id==q.id,GeneratedWorkedAnswer.status=='approved')):
        if older.id != row.id and str(older.id) not in referenced:
            older.status='superseded';older.revision+=1
            audit(db,principal.user.id,older,'superseded',f'Replaced by {row.id}')
    row.assets=assets;q.review_data=data;q.revision+=1
    q.reviewed_by=principal.user.id;q.reviewed_at=datetime.now(timezone.utc)
    audit(db,principal.user.id,row,'attached')
    db.commit()
    return {'questionRevision':q.revision,'assetIds':assets}


def capabilities(db,settings):
    from app.models import AIProviderAccount
    now=datetime.now(timezone.utc)
    accounts=db.scalars(select(AIProviderAccount).where(AIProviderAccount.enabled.is_(True))).all()
    configured=any(settings.openai_account_key(a.credential_alias) and a.health_status not in ('credit_exhausted','invalid_credential')
        and (a.cooldown_until is None or a.cooldown_until <= now) for a in accounts)
    return {'enabled':settings.worked_answers_enabled,'providerConfigured':bool(configured),
            'ready':settings.worked_answers_enabled and bool(configured)}
