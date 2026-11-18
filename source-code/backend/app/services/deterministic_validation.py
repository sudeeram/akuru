"""Authenticated server replay; durable append-only certificates in indexed AuditEvent.

The existing audit table supplies UUID, actor FK, timestamps and indexed
(action,target) lookup. No new table or schema migration is needed. Fixtures
are synthetic, bounded inputs; client verdicts never establish readiness.
"""
import copy
import hashlib
import json
import uuid
from datetime import datetime,timezone
from pydantic import BaseModel,ConfigDict,Field
from sqlalchemy import select
from app.errors import DomainError
from app.models import AuditEvent,DocumentBlock,DocumentAsset
from app.schemas.official_paper_reviews import ReviewQuestionData,SaveReviewQuestion
from app.services import deterministic_scoring as engine,marking_rules

ACTION='official_review.deterministic_validated'

class Case(BaseModel):
    model_config=ConfigDict(extra='forbid')
    answer:str=Field(min_length=1,max_length=3000)
    expectedMarks:int|None=Field(default=None,ge=0,le=200)
    expectedPoints:list[str]=Field(default_factory=list,max_length=200)
    requiresReview:bool=False
    holdout:bool=False

class Package(BaseModel):
    model_config=ConfigDict(extra='forbid')
    requestId:uuid.UUID
    partLabel:str=Field(min_length=1,max_length=40)
    expectedRevision:int=Field(ge=1)
    expectedEngineHash:str=Field(pattern=r'^[a-f0-9]{64}$')
    confirmSourceReviewed:bool
    sourceNotes:str=Field(min_length=20,max_length=4000)
    provenance:dict[str,str]=Field(default_factory=dict,max_length=10)
    cases:list[Case]=Field(min_length=4,max_length=200)


def canonical_rules(rules):
    result=copy.deepcopy(rules)
    if result.get('deterministic'):result['deterministic'].pop('certificateId',None)
    return result

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()

def runtime_hash(shared,prompt,marks,points,rules):
    # Normalize review-point defaults before binding frozen assessment rubrics.
    from app.schemas.official_paper_reviews import ReviewMarkingPoint
    normalized=[ReviewMarkingPoint.model_validate(p).model_dump(mode='json')for p in points]
    return digest(dict(shared=shared,prompt=prompt,marks=marks,points=normalized,rules=canonical_rules(rules)))

def binding(db,workspace,data,part):
    from .official_question_analyses import source_manifest
    sources=part.paperSources+part.schemeSources+part.reportSources
    blockids={s.blockId for s in sources if s.blockId};assetids={s.assetId for s in sources if s.assetId}|set(data.visualAssetIds)|set(part.visualAssetIds)
    blocks=[dict(id=str(b.id),text=b.text,latex=b.latex,kind=b.block_kind,bounds=b.bounding_box)for b in db.scalars(select(DocumentBlock).where(DocumentBlock.id.in_(blockids))).all()]
    assets=[dict(id=str(a.id),sha=a.sha256,metadata=a.asset_metadata)for a in db.scalars(select(DocumentAsset).where(DocumentAsset.id.in_(assetids))).all()]
    return digest(dict(runtime=runtime_hash(data.sharedStem,part.prompt,part.marks,[p.model_dump(mode='json')for p in part.markingPoints],part.scoringRules.model_dump(mode='json')),manifest=source_manifest(db,workspace),blocks=sorted(blocks,key=lambda b:b['id']),assets=sorted(assets,key=lambda a:a['id']),sources=[s.model_dump(mode='json')for s in sources]))

def certificate(db,workspace,row,data,part):
    config=part.scoringRules.deterministic
    if not config or not config.certificateId:return None
    run=db.get(AuditEvent,uuid.UUID(config.certificateId))
    if not run or run.action!=ACTION or run.target_id!=str(row.id):return None
    v=run.event_data
    if not v.get('passed')or v.get('part')!=part.label or v.get('engineHash')!=engine.engine_hash() or v.get('binding')!=binding(db,workspace,data,part):return None
    return run


def history(db,workspace,row):
    data=ReviewQuestionData.model_validate(row.review_data)
    return [dict(id=str(e.id),createdAt=e.created_at,**e.event_data,
        current=any(p.label==e.event_data.get('part')and certificate(db,workspace,row,data,p)is not None and p.scoringRules.deterministic.certificateId==str(e.id)for p in data.parts))
        for e in db.scalars(select(AuditEvent).where(AuditEvent.action==ACTION,AuditEvent.target_id==str(row.id)).order_by(AuditEvent.created_at.desc()).limit(100))]


def replay(data,part,package):
    points=[dict(pointId=p.code,criterion=p.text,maxMarks=1,dependsOn=p.dependsOn,followThrough=p.followThrough,acceptedAnswers=p.acceptedAnswers)for p in part.markingPoints]
    rules=part.scoringRules.model_dump(mode='json');engine.validate(points,part.marks,rules)
    cases=[]
    for sample in package.cases:
        actual=None;ids=[];review=False;reason=None
        try:actual,decisions,_=engine.recognize(sample.answer,points,part.marks,rules);ids=sorted(d.pointId for d in decisions if d.awarded)
        except DomainError as e:
            if e.code!='deterministic_requires_review':raise
            review=True;reason=e.message
        passed=review==sample.requiresReview and (review or actual==sample.expectedMarks and ids==sorted(sample.expectedPoints))
        cases.append(dict(**sample.model_dump(),actualMarks=actual,actualPoints=ids,actualRequiresReview=review,reason=reason,passed=passed))
    known={p.code for p in part.markingPoints}
    credited={i for c in cases if c['passed']and not c['actualRequiresReview']for i in c['actualPoints']}
    scores={c['actualMarks']for c in cases if c['passed']and not c['actualRequiresReview']}
    coverage=(known<=credited and {0,part.marks}<=scores and (part.marks<2 or any(0<s<part.marks for s in scores))
        and any(c['holdout']and c['passed']for c in cases)and any(c['requiresReview']and c['passed']for c in cases)
        and len({c['answer']for c in cases})==len(cases))
    return dict(passed=all(c['passed']for c in cases)and coverage,coverageComplete=coverage,cases=cases,noModelCalls=True,engine=engine.ENGINE,engineHash=engine.engine_hash())


def run(db,principal,paper_id,number,payload):
    from . import evidence_links,official_paper_reviews,paper_source_issues
    w,row,sourcehash=evidence_links._context(db,paper_id,number,lock=True)
    previous=db.get(AuditEvent,payload.requestId)
    requesthash=digest(payload.model_dump(mode='json'))
    if previous:
        if previous.action!=ACTION or previous.target_id!=str(row.id)or previous.actor_id!=principal.user.id or previous.event_data.get('requestHash')!=requesthash:raise DomainError('deterministic_request_conflict','Request ID already used.',409)
        existing_data=ReviewQuestionData.model_validate(row.review_data)
        existing_part=next((p for p in existing_data.parts if p.label==payload.partLabel),None)
        if previous.event_data.get('passed') and (not existing_part or not certificate(db,w,row,existing_data,existing_part)):
            raise DomainError('deterministic_certificate_stale','That validation is historical; run a fresh source-bound replay.',409)
        return dict(id=str(previous.id),**previous.event_data)
    if row.revision!=payload.expectedRevision:raise DomainError('review_conflict','Reload the current question before validating.',409)
    if not payload.confirmSourceReviewed or payload.expectedEngineHash!=engine.engine_hash():raise DomainError('deterministic_review_required','Confirm reviewed sources and the deployed engine hash.',409)
    data=ReviewQuestionData.model_validate(row.review_data);part=next((p for p in data.parts if p.label==payload.partLabel),None)
    if not part or part.responseType!='text'or part.status not in {'approved','ai_approved'}or row.status in {'needs_correction','excluded'}:raise DomainError('scoring_review_required','An approved typed subpart is required.',409)
    if not any(s.blockId for s in part.paperSources)or not any(s.blockId for s in part.schemeSources):raise DomainError('exact_block_required','Exact paper and scheme blocks are required.',409)
    from .question_auto_approval import current_accuracy
    current = current_accuracy(db,w,row)
    if not current:raise DomainError('deterministic_source_assessment_required','Refresh the source assessment after editing rules, then validate answers.',409)
    if paper_source_issues.blocking(current,part.label,paper_source_issues.decisions(db,[row.id])):raise DomainError('practice_source_issue','Resolve source/scoring issues before certification.',409)
    result=replay(data,part,payload)
    v=dict(**result,part=part.label,requestHash=requesthash,sourceNotes=payload.sourceNotes,provenance=payload.provenance,
        binding=binding(db,w,data,part),runtimeHash=runtime_hash(data.sharedStem,part.prompt,part.marks,[p.model_dump(mode='json')for p in part.markingPoints],part.scoringRules.model_dump(mode='json')),
        sourceHash=sourcehash,rubricRevision=row.revision,fixtureHash=digest([s.model_dump()for s in payload.cases]))
    event=AuditEvent(id=payload.requestId,actor_id=principal.user.id,action=ACTION,target_type='official_paper_review_question',target_id=str(row.id),event_data=v,created_at=datetime.now(timezone.utc));db.add(event);db.flush()
    if result['passed']:
        part.scoringRules.deterministic.certificateId=str(event.id)
        part.assessmentReadiness='automatic';part.assessmentReadinessReason='Deterministic server validation passed: '+str(event.id)
        official_paper_reviews.save_question(db,principal,paper_id,SaveReviewQuestion(number=number,expectedRevision=row.revision,status=row.status,data=data),commit=False)
    db.commit()
    return dict(id=str(event.id),**v)


def require_frozen_certificate(db,question):
    """Frozen rules still require a real server-created proof, never a self-asserted ID."""
    from app.schemas.marking_rules import MarkingRules
    parsed=MarkingRules.model_validate(question.rubric['scoringRules'])
    config=parsed.deterministic
    if config and config.parts:
        data=ReviewQuestionData.model_validate(dict(marks=question.marks,sharedStem=question.shared_stem,
            prompt=question.prompt,parts=[p.model_dump() for p in config.parts]))
        compiled, rules=marking_rules.compile_review(data)
        if digest(compiled)!=digest(question.rubric['markingPoints']) or digest(rules)!=digest(question.rubric['scoringRules']):
            raise DomainError('deterministic_certificate_required','Composite scoring context does not match its frozen rules.',409)
        for part in config.parts:
            require_frozen_certificate(db,type('FrozenPart',(),dict(shared_stem=question.shared_stem,prompt=part.prompt,marks=part.marks,rubric=dict(markingPoints=part.markingPoints,scoringRules=part.scoringRules))))
        return True
    if not config or not config.certificateId:raise DomainError('deterministic_certificate_required','Missing scoring certificate.',409)
    event=db.get(AuditEvent,uuid.UUID(config.certificateId))
    actual=runtime_hash(question.shared_stem,question.prompt,question.marks,question.rubric['markingPoints'],question.rubric['scoringRules'])
    if not event or event.action!=ACTION or not event.event_data.get('passed')or event.event_data.get('engineHash')!=engine.engine_hash()or event.event_data.get('runtimeHash')!=actual:
        raise DomainError('deterministic_certificate_required','Frozen rules no longer match their validated engine/certificate.',409)
    return event
