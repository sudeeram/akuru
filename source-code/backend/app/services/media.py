import hashlib
import html
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.ai.base import AIProviderError
from app.ai.image_router import ImageAccountRouter
from app.config import Settings
from app.errors import DomainError
from app.models import AuditEvent, Document, EducationalMedia, RetrievalChunk, TextbookGroup, TextbookTopic
from app.services.retrieval import authorize_student

PROMPT_VERSION = "illustration-v1"
SVG_VERSION = "akuru-svg-v1"

def _number(value, name, low=-10000, high=10000):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= float(value) <= high:
        raise DomainError("media_parameters_invalid", f"{name} must be a number from {low} to {high}.", 422)
    return float(value)

def _source(db: Session, subject_id: str, chunk_id: uuid.UUID):
    row = db.execute(select(RetrievalChunk, Document, TextbookTopic, TextbookGroup).join(Document, Document.id == RetrievalChunk.document_id).join(
        TextbookTopic, TextbookTopic.id == RetrievalChunk.topic_id).join(
        TextbookGroup, TextbookGroup.id == TextbookTopic.group_id).where(RetrievalChunk.id == chunk_id,
        RetrievalChunk.status == "active", RetrievalChunk.subject_id == subject_id,
        Document.review_state == "published", Document.removed_at.is_(None))).first()
    if not row: raise DomainError("media_source_invalid", "Choose active evidence from a published source in the same subject.", 409)
    return row

def _svg(kind: str, parameters: dict, title: str, alt: str) -> bytes:
    title, alt = html.escape(title), html.escape(alt)
    start = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400" role="img"><title>{title}</title><desc>{alt}</desc><rect width="640" height="400" fill="white"/><g stroke="#315f9e" stroke-width="4" fill="none">'
    if kind == "circuit_svg":
        voltage=_number(parameters.get("voltage", 6),"voltage",0,1000); resistance=_number(parameters.get("resistance", 3),"resistance",0.01,100000)
        body=f'<path d="M100 90H270M370 90H540V310H100V90"/><path d="M270 90l80-45"/><circle cx="420" cy="310" r="35"/><path d="M395 285l50 50m0-50l-50 50"/><path d="M165 290v40m25-55v70"/></g><g font-family="sans-serif" font-size="20" fill="#17365f"><text x="270" y="140">open switch</text><text x="130" y="375">{voltage:g} V</text><text x="455" y="275">{resistance:g} Ω</text></g>'
    elif kind == "forces_svg":
        left=_number(parameters.get("left",8),"left force",0,10000); right=_number(parameters.get("right",12),"right force",0,10000)
        body=f'<defs><marker id="a" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#315f9e"/></marker></defs><rect x="245" y="145" width="150" height="110" rx="10" fill="#e8f0fb"/><path d="M245 200H80" marker-end="url(#a)"/><path d="M395 200H560" marker-end="url(#a)"/></g><g font-family="sans-serif" font-size="22"><text x="105" y="180">{left:g} N</text><text x="475" y="180">{right:g} N</text><text x="292" y="210">object</text></g>'
    elif kind == "geometry_svg":
        a=_number(parameters.get("angleA",50),"angle A",1,178); b=_number(parameters.get("angleB",60),"angle B",1,178)
        if a+b >= 180: raise DomainError("media_parameters_invalid", "The two triangle angles must total less than 180 degrees.", 422)
        body=f'<path d="M100 320H550L300 60Z" fill="#e8f0fb"/></g><g font-family="sans-serif" font-size="24"><text x="135" y="300">{a:g}°</text><text x="485" y="300">{b:g}°</text><text x="292" y="115">{180-a-b:g}°</text><text x="210" y="380" font-size="16">Diagram not drawn to scale</text></g>'
    else:
        points=parameters.get("points")
        if not isinstance(points,list) or not 2 <= len(points) <= 30: raise DomainError("media_parameters_invalid", "A plot requires 2 to 30 [x, y] points.", 422)
        pairs=[(_number(p[0],"x"),_number(p[1],"y")) if isinstance(p,list) and len(p)==2 else (_number(None,"x"),0) for p in points]
        xs=[p[0] for p in pairs];ys=[p[1] for p in pairs];dx=max(xs)-min(xs) or 1;dy=max(ys)-min(ys) or 1
        coords=' '.join(f'{70+(x-min(xs))/dx*500:.1f},{330-(y-min(ys))/dy*260:.1f}' for x,y in pairs)
        body=f'<path d="M70 50V330H590"/></g><polyline points="{coords}" fill="none" stroke="#d43f5e" stroke-width="4"/><g fill="#d43f5e">'+''.join(f'<circle cx="{70+(x-min(xs))/dx*500:.1f}" cy="{330-(y-min(ys))/dy*260:.1f}" r="6"/>' for x,y in pairs)+'</g>'
    return (start+body+'</svg>').encode()

def _response(row: EducationalMedia, private=True):
    return {"id":row.id,"subjectId":row.subject_id,"topicId":row.topic_id,"sourceChunkId":row.source_chunk_id,
        "kind":row.kind,"title":row.title,"altText":row.alt_text,"prompt":row.prompt if private else "","promptVersion":row.prompt_version,
        "parameters":row.parameters if private else {},"sourceManifest":row.source_manifest,"provider":row.provider if private else "reviewed",
        "model":row.model if private else "","responseId":row.response_id if private else None,"contentType":row.content_type,"status":row.status,
        "reviewNotes":row.review_notes if private else "",
        "createdAt":row.created_at,"reviewedAt":row.reviewed_at,"contentUrl":f"/api/v1/media/{row.id}/content"}

def _save(db, storage, principal, payload, content, content_type, provider, model, response_id, prompt, status):
    chunk, document, topic, group = _source(db,payload.subjectId,payload.sourceChunkId); media_id=uuid.uuid4()
    key=f"media/{payload.subjectId}/{media_id}.{ 'svg' if content_type == 'image/svg+xml' else 'png'}"
    storage.put(key,content,content_type)
    manifest=[{"chunkId":str(chunk.id),"documentId":str(document.id),"documentTitle":document.title,
        "documentVersionId":str(chunk.document_version_id),"topicRef":topic.public_ref,"topicCode":topic.code,
        "groupCode":group.code,
        "page":chunk.page_number,"contentHash":chunk.content_hash}]
    row=EducationalMedia(id=media_id,subject_id=payload.subjectId,topic_id=topic.id,source_chunk_id=chunk.id,
        kind=payload.kind if hasattr(payload,"kind") else "conceptual_image",title=payload.title,alt_text=payload.altText,
        prompt=prompt,prompt_version=SVG_VERSION if provider=="akuru" else PROMPT_VERSION,parameters=getattr(payload,"parameters",{}),
        source_manifest=manifest,provider=provider,model=model,response_id=response_id,object_key=key,content_type=content_type,
        checksum=hashlib.sha256(content).hexdigest(),status=status,created_by=principal.user.id)
    db.add(row);db.commit();db.refresh(row);return _response(row)

def deterministic(db,storage,principal,payload):
    _source(db,payload.subjectId,payload.sourceChunkId)
    content=_svg(payload.kind,payload.parameters,payload.title,payload.altText)
    return _save(db,storage,principal,payload,content,"image/svg+xml","akuru",SVG_VERSION,None,
        json.dumps(payload.parameters,sort_keys=True),"published")

def illustration(db,storage,settings,principal,payload):
    chunk,document,topic,group=_source(db,payload.subjectId,payload.sourceChunkId)
    grounded=("Create a clear educational conceptual illustration for an iGCSE learner. No decorative labels, marks, answers, "
        "logos, copyrighted characters, or claims beyond the supplied source. Prompt: "+payload.prompt+"\nApproved source context: "+chunk.content)
    try:
        with Session(bind=db.get_bind()) as provider_db: result=ImageAccountRouter(provider_db,settings).generate(grounded,uuid.uuid4())
    except AIProviderError as exc: raise DomainError(exc.code,str(exc),503) from exc
    return _save(db,storage,principal,payload,result.content,result.content_type,result.provider,result.model,
        result.response_id,grounded,"pending_review")

def list_media(db,principal,student_id=None,subject_id=None):
    query=select(EducationalMedia)
    if principal.user.role != "admin":
        if not student_id or not subject_id: raise DomainError("media_scope_required","Student and subject are required.",422)
        topics=authorize_student(db,principal,student_id,subject_id)
        query=query.where(EducationalMedia.status=="published",EducationalMedia.subject_id==subject_id,EducationalMedia.topic_id.in_(topics))
    rows=db.scalars(query.order_by(EducationalMedia.created_at.desc())).all()
    return {"media":[_response(row,principal.user.role == "admin") for row in rows]}

def sources(db,subject_id):
    rows=db.execute(select(RetrievalChunk,Document,TextbookTopic,TextbookGroup).join(Document,Document.id==RetrievalChunk.document_id).join(
        TextbookTopic,TextbookTopic.id==RetrievalChunk.topic_id).join(TextbookGroup,TextbookGroup.id==TextbookTopic.group_id).where(RetrievalChunk.status=="active",
        RetrievalChunk.subject_id==subject_id,Document.review_state=="published",Document.removed_at.is_(None)).order_by(
        TextbookGroup.sequence,TextbookTopic.sequence,RetrievalChunk.page_number).limit(200)).all()
    return [{"id":chunk.id,"subjectId":chunk.subject_id,"topicRef":topic.public_ref,"topicCode":topic.code,
        "topicTitle":topic.title,"groupCode":group.code,"documentTitle":document.title,"page":chunk.page_number,
        "excerpt":chunk.content[:240]} for chunk,document,topic,group in rows]

def review(db,principal,media_id,payload):
    row=db.get(EducationalMedia,media_id)
    if not row: raise DomainError("media_not_found","Educational media not found.",404)
    if row.provider == "akuru": raise DomainError("media_review_not_required","Deterministic visuals are published from validated parameters.",409)
    if row.status != "pending_review": raise DomainError("media_review_complete","This media item has already been reviewed.",409)
    row.status=payload.decision;row.review_notes=payload.notes;row.reviewed_by=principal.user.id;row.reviewed_at=datetime.now(timezone.utc)
    db.add(AuditEvent(actor_id=principal.user.id,action="media.review",target_type="educational_media",target_id=str(row.id),
        event_data={"decision":payload.decision,"notes":payload.notes}));db.commit();db.refresh(row);return _response(row)

def content(db,storage,principal,media_id,student_id=None):
    row=db.get(EducationalMedia,media_id)
    if not row: raise DomainError("media_not_found","Educational media not found.",404)
    if principal.user.role != "admin":
        if row.status != "published" or not student_id: raise DomainError("media_not_found","Educational media not found.",404)
        try: eligible_topics=authorize_student(db,principal,student_id,row.subject_id)
        except DomainError as exc: raise DomainError("media_not_found","Educational media not found.",404) from exc
        if row.topic_id not in eligible_topics: raise DomainError("media_not_found","Educational media not found.",404)
    return storage.get(row.object_key,row.content_type)
