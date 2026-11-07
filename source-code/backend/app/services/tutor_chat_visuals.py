"""Approved stored visual selection. No generation, rendering or remote fetching."""
import re
import uuid
from sqlalchemy import select
from app.errors import DomainError
from app.models import Document,DocumentAsset,DocumentBlock,TextbookTopicVisualAsset,EducationalMedia
from app.schemas.tutor_agent import TutorVisual
from app.services import tutor_sources
from app.services.assessment_access import TutorCapability,require_tutor_access

VERSION='approved-chat-visuals-v1'


def generation_requested(message):
    return bool(re.search(r'\b(?:draw|generate|create|make)\b.{0,35}\b(?:image|picture|diagram|graph|illustration|svg)\b|\b(?:image|picture|diagram)\b.{0,20}\b(?:using|with)\s+ai\b',message,re.I))


def meaningful(kind,caption,alt,metadata=None):
    classification=(metadata or {}).get('visualClassification','')
    if classification in {'text_only','page','decorative','prose'}: return False
    if kind not in {'image','diagram','table','conceptual_image','circuit_svg','forces_svg','geometry_svg','plot_svg'}: return False
    description=caption+' '+alt
    if not caption.strip() or not alt.strip(): return False
    if re.search(r'\b(?:text.only|paragraph screenshot|page screenshot|page render|screenshot of (?:text|a paragraph)|decorative)\b',description,re.I):return False
    return True


def _gate(db,settings,principal,session,topic_id):
    require_tutor_access(db,settings,principal.user.id,TutorCapability.TOOLS,session.subject_id,'tutor_visuals',topic_id=topic_id)


def candidates(db,settings,principal,session):
    scopes=tutor_sources.authorized_topics(db,settings,principal,session)
    result=[]
    for topic,version,book in scopes:
        try:_gate(db,settings,principal,session,topic.id)
        except DomainError as error:
            if error.status_code not in {403,409}:raise
            continue
        for entry in version.extraction_manifest.get('visualAssets',[]):
            try:asset_id=uuid.UUID(entry['documentAssetId'])
            except (ValueError,KeyError):continue
            selected=db.scalar(select(TextbookTopicVisualAsset).where(TextbookTopicVisualAsset.topic_id==topic.id,
                TextbookTopicVisualAsset.document_asset_id==asset_id,TextbookTopicVisualAsset.status=='approved'))
            asset=db.get(DocumentAsset,asset_id)
            block=db.get(DocumentBlock,selected.block_id) if selected else None
            document=db.get(Document,uuid.UUID(entry['documentId'])) if entry.get('documentId') else None
            if not selected or not selected.reviewed_by or not selected.reviewed_at or not asset or not block or not document or document.removed_at or document.review_state != "published":continue
            if asset.asset_kind=='page_render' or asset.sha256!=entry.get('checksum') or str(asset.document_version_id)!=entry.get('documentVersionId'):continue
            if selected.caption!=entry.get('caption') or selected.alt_text!=entry.get('altText'):continue
            if not meaningful(entry.get('kind'),selected.caption,selected.alt_text,asset.asset_metadata):continue
            result.append((topic,version,book,entry,asset))
    return result


def concept_match(query, description):
    # A newly named concept wins over old context; generic words alone cannot
    # select an unrelated scientific figure.
    concepts = [
        (r'\b(?:lung|alveol|gas exchange)\w*', r'lung|alveol|gas exchange'),
        (r'\bphotosynth\w*', r'photosynth|chloroplast'),
        (r'\brespir\w*', r'respir|mitochond'),
        (r'\b(?:cell|cells|nucleus|nuclei|cytoplasm|organelle)\b', r'cell|nucleus|nuclei|organelle'),
        (r'\bevaporat\w*', r'evaporat'), (r'\bboil\w*', r'boil'),
        (r'\bdiffus\w*', r'diffus'), (r'\bosmos\w*', r'osmos|membrane'),
        (r'\bchromatograph\w*', r'chromatograph'),
        (r'\b(?:melting|freezing)\b', r'melt|freez'),
        (r'\b(?:sublim|deposit)\w*', r'sublim|deposit'),
        (r'\b(?:liquids?\s+flow|why.{0,12}liquids?.{0,12}flow|particle model|particles? diagram)\b', r'arrangement|liquid particles|solid particles'),
    ]
    latest=query.split('Current follow-up:')[-1]
    selected=[pattern for trigger,pattern in concepts if re.search(trigger,latest,re.I)]
    if not selected:
        anchor=re.search(r'Earlier question: ([^\n]+)',query)
        context=anchor.group(1) if anchor else query
        selected=[pattern for trigger,pattern in concepts if re.search(trigger,context,re.I)]
    focus=latest if any(re.search(trigger,latest,re.I) for trigger,_ in concepts) else (re.search(r'Earlier question: ([^\n]+)',query).group(1) if re.search(r'Earlier question: ([^\n]+)',query) else query)
    if re.search(r'\b(?:nucleus|nuclei)\b',focus,re.I):
        return bool(re.search(r'\b(?:nucleus|nuclei)\b',description,re.I))
    if selected:return any(re.search(pattern,description,re.I) for pattern in selected)
    if re.search(r'\b(?:changes? of state|states? of matter)\b',query,re.I):
        return bool(re.search(r'arrangement|change of state|melt|freez|sublim|boil|evaporat',description,re.I))
    generic={'diagram','figure','image','picture','graph','show','new','generate','explain','liquid','gas','solid','particles','particle','answer','question','help','label','labelled','work','create','draw','make'}
    return bool((tutor_sources._terms(query)-generic) & tutor_sources._terms(description))


def select_visuals(db,settings,principal,session,query,previous_asset_ids=()):
    available=candidates(db,settings,principal,session)
    terms=tutor_sources._terms(query)-{'human','approved','generate','new','cellular','faster','help','please'}
    figures=set(re.findall(r'\bfig(?:ure)?\.?\s*(\d+(?:\.\d+)+)\b',query,re.I))
    anchor=re.search(r'Earlier question: ([^\n]+)',query)
    focus=anchor.group(1) if anchor else query
    latest=query.split('Current follow-up:')[-1]
    if re.search(r'\b(?:human|animal|plant)\s+cells?\b',latest,re.I):focus=latest
    ranked=[]
    for topic,version,book,entry,asset in available:
        description=entry['caption']+' '+entry['altText']
        if re.search(r'\b(?:human|animal)\s+cells?\b',focus,re.I) and not re.search(r'\bplant\b',focus,re.I):
            if re.search(r'\b(?:plants?|chloroplasts?|cell walls?|leaves|leaf|palisade|mesophyll|stomata|guard cells?)\b',description,re.I) and not re.search(r'\b(?:human|animal)\b',description,re.I):continue
        ids=set(re.findall(r'\bfig(?:ure)?\.?\s*(\d+(?:\.\d+)+)\b',description,re.I))
        overlap=terms & tutor_sources._terms(description)
        if figures:
            if not figures & ids:continue
            score=100
        else:
            if not concept_match(query,description):continue
            # No generic prose-page or unrelated newest-asset fallback.
            score=len(overlap-{'figure','diagram','image','picture','labelled','labels','graph'})
            if re.search(r'\b(?:cells?|nucleus|nuclei)\b',query,re.I):
                if re.search(r'\b(?:structure|organelles?|typical|electron micrograph)\b',description,re.I):score+=20
                if re.search(r'\b(?:nucleus|nuclei)\b',query,re.I) and re.search(r'\b(?:nucleus|nuclei)\b',description,re.I):score+=10
                if not re.search(r'\b(?:division|kidney|tubule|embryo|zygote)\b',query,re.I) and re.search(r'\b(?:division|kidney|tubule|embryo|zygote)\b',description,re.I):continue
            if not score:continue
        ranked.append((score,topic,version,book,entry,asset))
    if figures and len({r[1].id for r in ranked})>1:
        return [],'ambiguous_figure'
    explicit=bool(re.search(r'\b(?:show|image|diagram|figure|picture|graph)\b',query,re.I))
    visuals=[];seen=set()
    for _,topic,version,book,entry,asset in sorted(ranked,key=lambda r:(-r[0],str(r[5].id))):
        if asset.id in seen or (str(asset.id) in previous_asset_ids and not explicit):continue
        seen.add(asset.id)
        label=entry.get('printedPageLabel') or f"PDF {entry['pageNumber']}"
        visuals.append(TutorVisual(title=entry['caption'],altText=entry['altText'],visualType='official_source',kind=entry['kind'],
            contentUrl=f'/api/v1/tutoring/sessions/{session.public_ref}/approved-visuals/{asset.id}',
            readableFallback=entry['altText'],sourceLabel=f'{book.title} · {topic.title} · Page {label}',
            provenance={'origin':'official_textbook','assetId':str(asset.id),'topicRef':topic.public_ref,
                'topicContentVersion':version.version_number,'reviewState':'approved','checksum':asset.sha256},sourceRefs=[]))
        if len(visuals)==2:break
    # Previously generated media must have independent human review and an
    # authorised current source; chat never creates it or marks it approved.
    if not visuals and not figures and not ranked:
        allowed={t.id for t,_,_ in tutor_sources.authorized_topics(db,settings,principal,session)}
        rows=db.scalars(select(EducationalMedia).where(EducationalMedia.topic_id.in_(allowed),EducationalMedia.subject_id==session.subject_id,
            EducationalMedia.status=='published',EducationalMedia.reviewed_at.is_not(None),EducationalMedia.reviewed_by.is_not(None))).all() if allowed else []
        for row in rows:
            if not meaningful(row.kind,row.title,row.alt_text,row.parameters) or not concept_match(query,row.title+' '+row.alt_text):continue
            try:
                _gate(db,settings,principal,session,row.topic_id)
                source=tutor_sources.get_citation(db,settings,principal,session.public_ref,f'citation_{row.source_chunk_id.hex}')
            except DomainError:continue
            visuals.append(TutorVisual(title=row.title,altText=row.alt_text,visualType='explanatory',kind=row.kind,
                contentUrl=f'/api/v1/tutoring/sessions/{session.public_ref}/media/{row.id}',readableFallback=row.alt_text,
                sourceLabel=f'Admin-approved explanatory aid based on {source.textbookTitle} · {source.pageReference}',
                provenance={'origin':'reviewed_generation' if row.provider!='akuru' else 'reviewed_stored_diagram','reviewState':'published',
                    'assetId':str(row.id),'generator':row.provider,'model':row.model,'checksum':row.checksum},sourceRefs=[source.citationRef]))
            break
    return visuals,('available' if visuals else 'no_approved_match')


def open_visual(db,settings,principal,storage,session_ref,asset_id):
    session=tutor_sources._session(db,settings,principal,session_ref)
    for _,_,_,_,asset in candidates(db,settings,principal,session):
        if asset.id==asset_id:
            return storage.get(asset.object_key,asset.mime_type)
    raise DomainError('tutor_visual_not_found','Approved visual not found.',404)


def open_media(db,settings,principal,storage,session_ref,media_id):
    session=tutor_sources._session(db,settings,principal,session_ref)
    row=db.get(EducationalMedia,media_id)
    if not row or row.status!='published' or not row.reviewed_at or not row.reviewed_by or row.subject_id!=session.subject_id or not meaningful(row.kind,row.title,row.alt_text,row.parameters):
        raise DomainError('tutor_media_not_found','Approved visual not found.',404)
    _gate(db,settings,principal,session,row.topic_id)
    tutor_sources.get_citation(db,settings,principal,session_ref,f'citation_{row.source_chunk_id.hex}')
    return storage.get(row.object_key,row.content_type)
