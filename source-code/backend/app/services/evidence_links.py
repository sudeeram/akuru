"""Audited exact-source proposals. Never publish papers or reuse stale confidence."""
from copy import deepcopy
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib,json,re,uuid
import pymupdf
from sqlalchemy import select,func
from app.errors import DomainError
from app.models import AuditEvent,DocumentBlock,DocumentPage,DocumentVersion,OfficialPaperReviewQuestion
from app.schemas.official_paper_reviews import ReviewQuestionData
from app.services import official_paper_reviews as reviews,official_question_analyses as analyses

VERSION='exact-evidence-v1'

def _audit(db,principal,paper_id,action,data,event_id=None):
    row=AuditEvent(id=event_id or uuid.uuid4(),actor_id=principal.user.id,action=action,
        target_type='official_evidence_links',target_id=str(paper_id),event_data=data)
    db.add(row);db.flush();return row

def _context(db,paper_id,number,lock=False):
    workspace=reviews._workspace(db,paper_id);reviews._validate_bound_versions(db,workspace)
    if lock:db.refresh(workspace,with_for_update=True)
    query=select(OfficialPaperReviewQuestion).where(OfficialPaperReviewQuestion.workspace_id==workspace.id,OfficialPaperReviewQuestion.number==number)
    row=db.scalar(query.with_for_update()if lock else query)
    if not row:raise DomainError('question_not_found','Choose a saved question.',404)
    digest=analyses.content_hash(db,row,analyses.source_manifest(db,workspace))
    return workspace,row,digest

def _fresh(row,digest,revision,expected_hash):
    if row.revision!=revision or digest!=expected_hash:
        raise DomainError('evidence_conflict','This question or its source evidence changed. Analyse it again before applying links.',409)

def _words(text):return re.findall(r'[a-z0-9]+',text.casefold())

def _score(text,target):
    a,b=_words(text),_words(target)
    if not a or not b:return 0
    # Exactness, not isolated keyword overlap, is required for automatic use.
    return round(100*SequenceMatcher(None,a,b,autojunk=False).ratio())

def _snapshot(page,block):
    return dict(page=page.page_number,blockId=str(block.id),assetId=str(page.render_asset_id)if page.render_asset_id else None,
        normalizedBounds={k:block.bounding_box[k]/(page.width_points if k.startswith('x')else page.height_points)for k in ['x0','y0','x1','y1']} if all(k in block.bounding_box for k in ['x0','y0','x1','y1']) else None,
        bounds=block.bounding_box,text=block.text,sourceFingerprint=hashlib.sha256(json.dumps(dict(text=block.text,bounds=block.bounding_box,kind=block.block_kind),sort_keys=True).encode()).hexdigest())

def _region(storage,version,page,bounds):
    source=storage.get(version.object_key,version.mime_type)
    if hashlib.sha256(source.content).hexdigest()!=version.sha256:
        raise DomainError('evidence_source_checksum','The stored source checksum changed. Restore or review the source before linking.',409)
    try:
        with pymupdf.open(stream=source.content,filetype='pdf')as pdf:
            p=pdf[page.page_number-1];r=p.rect
            clip=pymupdf.Rect(bounds['x0']*r.width,bounds['y0']*r.height,bounds['x1']*r.width,bounds['y1']*r.height)
            if clip.width*clip.height>2_000_000:raise DomainError('evidence_region_too_large','Select a smaller source region.',422)
            return p.get_textbox(clip).strip(),dict(zip(('x0','y0','x1','y1'),tuple(clip)))
    except (IndexError,pymupdf.FileDataError,FileNotFoundError)as exc:
        raise DomainError('evidence_source_unavailable','The original source page is unavailable.',409)from exc

def _events(db,paper_id):
    return db.scalars(select(AuditEvent).where(AuditEvent.target_type=='official_evidence_links',AuditEvent.target_id==str(paper_id)).order_by(AuditEvent.created_at,AuditEvent.id)).all()

def get_run(db,paper_id,run_id,events=None):
    if events is None:
        reviews._workspace(db,paper_id)
        events=_events(db,paper_id)
    run=next((event for event in events if event.id==run_id),None)
    if not run or run.target_type!='official_evidence_links' or run.target_id!=str(paper_id)or run.action!='official_review.evidence_proposed':
        raise DomainError('evidence_run_not_found','Evidence proposal not found.',404)
    result=deepcopy(run.event_data);result.pop('request',None);result['id']=str(run.id)
    states={}
    for event in events:
        if event.event_data.get('runId')==str(run.id):
            for pid in event.event_data.get('proposalIds',[]):states[pid]=event.event_data.get('decision')
    for proposal in result['proposals']:
        if proposal['id']in states:proposal['status']='linked'if states[proposal['id']]=='apply'else'rejected'
    return result

def listing(db,paper_id,number=None):
    reviews._workspace(db,paper_id)
    events=_events(db,paper_id)
    runs=[e for e in events if e.action=='official_review.evidence_proposed' and (number is None or e.event_data['number']==number)]
    return [get_run(db,paper_id,e.id,events)for e in runs[-30:]]

def propose(db,storage,principal,paper_id,payload):
    existing=db.get(AuditEvent,payload.requestId)
    if existing:
        if existing.event_data.get('request')!=payload.model_dump(mode='json'):
            raise DomainError('evidence_request_conflict','This request ID was already used for a different proposal.',409)
        return get_run(db,paper_id,payload.requestId)
    workspace,row,digest=_context(db,paper_id,payload.number)
    _fresh(row,digest,payload.expectedRevision,payload.expectedContentHash)
    parts={p['label']:p for p in row.review_data['parts']};proposals=[]
    manifest=analyses.source_manifest(db,workspace)
    for part in parts.values():
        for role in ['paper','scheme']:
            version_id=getattr(workspace,role+'_version_id')
            if not version_id:continue
            inputs=[s for s in payload.selections if s.part==part['label']and s.role==role]
            if not inputs and payload.selections:continue
            target=part['prompt']if role=='paper'else' '.join(p['text']for p in part['markingPoints'])
            pages={s['page']for s in part[role+'Sources']}
            if not inputs:
                candidates=[]
                for block,page in db.execute(select(DocumentBlock,DocumentPage).join(DocumentPage,DocumentPage.id==DocumentBlock.page_id).where(DocumentBlock.document_version_id==version_id,DocumentPage.page_number.in_(pages),DocumentBlock.block_kind.in_(['question','subpart','paragraph','table']))):
                    score=_score(block.text,target)
                    if score>=45:candidates.append((score,block,page))
                candidates.sort(key=lambda x:(-x[0],str(x[1].id)))
                if candidates:
                    score,block,page=candidates[0]
                    unambiguous=score>=98 and (len(candidates)==1 or score-candidates[1][0]>=10)and not block.needs_review and len(_words(target))>=6
                    proposals.append(dict(id=str(uuid.uuid4()),part=part['label'],role=role,documentVersionId=str(version_id),**_snapshot(page,block),confidence=score,
                        status='matched'if unambiguous else'ambiguous',autoEligible=unambiguous,reason='Exact reviewed text match.'if unambiguous else'Candidate text match; verify the complete subpart and rubric before linking.',sourceVerified=unambiguous))
                else:
                    proposals.append(dict(id=str(uuid.uuid4()),part=part['label'],role=role,documentVersionId=str(version_id),status='missing',confidence=0,autoEligible=False,sourceVerified=False,reason='No exact source block found. Select or import a focused original-source region.'))
                continue
            for selection in inputs:
                page=db.scalar(select(DocumentPage).where(DocumentPage.document_version_id==version_id,DocumentPage.page_number==selection.page))
                if not page:raise DomainError('invalid_source_page','The selection is not in the bound source version.',422)
                if selection.blockId:
                    block=db.get(DocumentBlock,selection.blockId)
                    if not block or block.page_id!=page.id or block.document_version_id!=version_id:
                        raise DomainError('invalid_source_block','The block must belong to the selected source and page.',422)
                    data=_snapshot(page,block)
                else:
                    version=db.get(DocumentVersion,version_id);text,bounds=_region(storage,version,page,selection.bounds.model_dump())
                    if not text:
                        proposals.append(dict(id=str(uuid.uuid4()),part=part['label'],role=role,documentVersionId=str(version_id),page=page.page_number,bounds=bounds,normalizedBounds=selection.bounds.model_dump(),text='',confidence=0,status='missing',autoEligible=False,sourceVerified=False,reason='This region has no native text. Use visual review for a diagram/grid, or review OCR before linking it as exact text evidence.'))
                        continue
                    data=dict(page=page.page_number,blockId=None,assetId=str(page.render_asset_id)if page.render_asset_id else None,bounds=bounds,normalizedBounds=selection.bounds.model_dump(),text=text,sourceFingerprint=hashlib.sha256(text.encode()).hexdigest())
                if len(data['text'])>20000:raise DomainError('evidence_text_limit','Select a focused source region.',422)
                proposals.append(dict(id=str(uuid.uuid4()),part=part['label'],role=role,documentVersionId=str(version_id),**data,confidence=selection.confidence,status='matched'if selection.sourceVerified else'ambiguous',autoEligible=False,sourceVerified=selection.sourceVerified,reason=selection.reason))
    if any(s.part not in parts for s in payload.selections):raise DomainError('invalid_evidence_part','Choose an existing subpart.',422)
    data=dict(number=row.number,revision=row.revision,contentHash=digest,sourceManifest=manifest,version=VERSION,createdAt=datetime.now(timezone.utc).isoformat(),request=payload.model_dump(mode='json'),provenance=[p.model_dump(mode='json')for p in payload.provenance]or[dict(role=r,method='deterministic',notes='Text matching only; no model call.')for r in ['paper','scheme']],proposals=proposals)
    _audit(db,principal,paper_id,'official_review.evidence_proposed',data,payload.requestId);db.commit()
    return get_run(db,paper_id,payload.requestId)

def decide(db,storage,principal,paper_id,run_id,payload):
    if len(payload.proposalIds)!=len(set(payload.proposalIds)):
        raise DomainError('invalid_evidence_selection','Choose distinct proposals.',422)
    workspace,row,digest=_context(db,paper_id,get_run(db,paper_id,run_id)['number'],lock=True)
    run=get_run(db,paper_id,run_id);selected=[p for p in run['proposals']if p['id']in {str(i)for i in payload.proposalIds}]
    if len(selected)!=len(set(payload.proposalIds)):raise DomainError('invalid_evidence_selection','Choose distinct proposals in this run.',422)
    if all(p['status']==('linked'if payload.decision=='apply'else'rejected')for p in selected):return dict(run=run,review=reviews._response(db,workspace),alreadyApplied=True)
    if any(p['status']in {'linked','rejected'}for p in selected):raise DomainError('evidence_already_decided','Choose only undecided proposals; prepare a new run to supersede an earlier decision.',409)
    _fresh(row,digest,payload.expectedRevision,payload.expectedContentHash)
    _fresh(row,digest,run['revision'],run['contentHash'])
    if run['sourceManifest']!=analyses.source_manifest(db,workspace):raise DomainError('evidence_source_changed','The bound source changed.',409)
    if payload.decision=='reject':
        _audit(db,principal,paper_id,'official_review.evidence_rejected',dict(runId=str(run_id),proposalIds=[p['id']for p in selected],decision='reject'));db.commit()
        return dict(run=get_run(db,paper_id,run_id),review=reviews._response(db,workspace),alreadyApplied=False)
    if row.status=='approved' or any(p['status']=='approved'for p in row.review_data['parts']):
        raise DomainError('reopen_required','Reopen the human-approved question/subparts before changing their exact source evidence.',409)
    if not payload.confirmSourceReview and not payload.autoOnly:
        raise DomainError('evidence_review_required','Confirm you checked the selected source regions before linking.',409)
    if any(p['status']=='missing' or (payload.autoOnly and not p['autoEligible'])for p in selected):
        raise DomainError('evidence_ambiguous','Only exact, unambiguous reviewed matches can be applied automatically.',409)
    before=deepcopy(row.review_data);data=deepcopy(before);parts={p['label']:p for p in data['parts']}
    for proposal in selected:
        version_id=uuid.UUID(proposal['documentVersionId']);page=db.scalar(select(DocumentPage).where(DocumentPage.document_version_id==version_id,DocumentPage.page_number==proposal['page']))
        if proposal.get('blockId'):
            block=db.get(DocumentBlock,uuid.UUID(proposal['blockId']))
            if not block or _snapshot(page,block)['sourceFingerprint']!=proposal['sourceFingerprint']:
                raise DomainError('evidence_block_changed','A source block changed. Analyse again.',409)
        else:
            version=db.get(DocumentVersion,version_id);text,bounds=_region(storage,version,page,proposal['normalizedBounds'])
            if hashlib.sha256(text.encode()).hexdigest()!=proposal['sourceFingerprint']:raise DomainError('evidence_region_changed','The source region changed.',409)
            key=hashlib.sha256(json.dumps(dict(version=str(version_id),role=proposal['role'],bounds=bounds,text=text),sort_keys=True).encode()).hexdigest()
            block=next((b for b in db.scalars(select(DocumentBlock).where(DocumentBlock.page_id==page.id))if b.block_metadata.get('exactEvidenceKey')==key),None)
            if block is None:
                sequence=(db.scalar(select(func.max(DocumentBlock.sequence_number)).where(DocumentBlock.page_id==page.id))or 0)+1
                block=DocumentBlock(document_version_id=version_id,page_id=page.id,sequence_number=sequence,block_kind='subpart',text=text,bounding_box=bounds,extraction_method='source_region',confidence=proposal['confidence']/100,needs_review=False,block_metadata=dict(exactEvidenceKey=key,sourceVersionSha256=version.sha256,runId=str(run_id),number=row.number,part=proposal['part'],role=proposal['role'],provenance=run['provenance'],sourceReview='Source association confirmed through Admin workflow; provenance distinguishes AI/manual review. Not human question approval.'))
                db.add(block);db.flush()
        ref=dict(page=page.page_number,blockId=str(block.id),assetId=str(page.render_asset_id)if page.render_asset_id else None)
        refs=parts[proposal['part']][proposal['role']+'Sources']
        if not any(s.get('blockId')==ref['blockId']for s in refs):refs.append(ref)
    for part in data['parts']:
        if part['status']=='ai_approved':part['status']='unreviewed'
    if row.status=='ai_approved':row.status='unreviewed'
    reviews._validate_question(db,workspace,row.status,ReviewQuestionData.model_validate(data),before,row.number)
    row.review_data=data;row.revision+=1
    _audit(db,principal,paper_id,'official_review.evidence_applied',dict(runId=str(run_id),proposalIds=[p['id']for p in selected],decision='apply',previous=before,after=data,questionRevision=row.revision,previousContentHash=digest))
    db.commit()
    return dict(run=get_run(db,paper_id,run_id),review=reviews._response(db,workspace),alreadyApplied=False)


def preview(db,storage,paper_id,run_id,proposal_id):
    run=get_run(db,paper_id,run_id)
    p=next((p for p in run['proposals']if p['id']==str(proposal_id)),None)
    if not p or not p.get('bounds'):raise DomainError('evidence_preview_missing','No source region is available.',404)
    version=db.get(DocumentVersion,uuid.UUID(p['documentVersionId']))
    original=storage.get(version.object_key,version.mime_type)
    with pymupdf.open(stream=original.content,filetype='pdf')as pdf:
        page=pdf[p['page']-1];clip=pymupdf.Rect(*[p['bounds'][k]for k in ['x0','y0','x1','y1']])
        scale=min(1.5,1800/max(clip.width,clip.height))
        return page.get_pixmap(matrix=pymupdf.Matrix(scale,scale),clip=clip,alpha=False).tobytes('png')
