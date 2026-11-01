import uuid
import math
import re
import unicodedata
from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import DomainError
from app.models import (
    Document, DocumentAsset, DocumentBlock, DocumentPage, DocumentVersion, RetrievalChunk,
    Textbook, TextbookGroup, TextbookTopic, TextbookTopicContentVersion, TutorSession,
)
from app.schemas.tutor_sources import TutorCitation, TutorCitationContextResponse, TutorSourceSearchResponse
from app.security import Principal
from app.services import curriculum_plans, tutor_sessions
from app.services.assessment_access import TutorCapability, require_tutor_access
from app.services.embeddings import embed_texts
from app.storage.base import ObjectStorage, StoredObject


def _chunk_id(citation_ref: str) -> uuid.UUID:
    if not citation_ref.startswith("citation_"):
        raise DomainError("tutor_citation_not_found", "Citation not found.", 404)
    try:
        return uuid.UUID(hex=citation_ref.removeprefix("citation_"))
    except ValueError as error:
        raise DomainError("tutor_citation_not_found", "Citation not found.", 404) from error


def _session(db: Session, settings: Settings, principal: Principal, session_ref: str) -> TutorSession:
    row = tutor_sessions._owned_session(db, principal.user.id, session_ref)
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS,
                         row.subject_id, "tutor_sources", topic_id=row.active_topic_id)
    if row.status != "active":
        raise DomainError("tutor_session_ended", "This tutor session has ended.", 409)
    coverage = curriculum_plans.student_coverage(db, principal.user.id, row.subject_id)
    active = db.get(TextbookTopic, row.active_topic_id)
    if coverage.status != "ready" or not active or active.public_ref not in {
        item.topicRef for item in coverage.coveredTopics
    }:
        raise DomainError("tutor_topic_not_eligible", "The active Tutor topic is no longer eligible.", 409)
    return row


def _published_version(db: Session, topic: TextbookTopic) -> TextbookTopicContentVersion | None:
    return db.scalar(select(TextbookTopicContentVersion).where(
        TextbookTopicContentVersion.topic_id == topic.id,
        TextbookTopicContentVersion.status == "published",
    ).order_by(TextbookTopicContentVersion.version_number.desc()))


def _asset(db: Session, chunk: RetrievalChunk, page: DocumentPage) -> DocumentAsset | None:
    asset_id = chunk.source_asset_id or page.render_asset_id
    asset = db.get(DocumentAsset, asset_id) if asset_id else None
    return asset if asset and asset.document_version_id == chunk.document_version_id else None


def _citation(db: Session, session: TutorSession, chunk: RetrievalChunk,
              confidence: float) -> TutorCitation:
    topic = db.get(TextbookTopic, session.active_topic_id)
    group = db.get(TextbookGroup, topic.group_id)
    book = db.get(Textbook, topic.textbook_id)
    document = db.get(Document, chunk.document_id)
    document_version = db.get(DocumentVersion, chunk.document_version_id)
    block = db.get(DocumentBlock, chunk.source_item_id)
    page = db.scalar(select(DocumentPage).where(
        DocumentPage.document_version_id == chunk.document_version_id,
        DocumentPage.page_number == chunk.page_number))
    if not document or document.review_state != "published" or document.removed_at or not document_version \
            or not block or block.needs_review or not page:
        raise DomainError("tutor_citation_not_found", "Citation not found.", 404)
    asset = _asset(db, chunk, page)
    if not asset:
        raise DomainError("tutor_citation_asset_missing", "The authorized citation image is unavailable.", 409)
    label = page.printed_page_label or page.page_metadata.get("printedPageLabel")
    citation_ref = f"citation_{chunk.id.hex}"
    base = f"/api/v1/tutoring/sessions/{session.public_ref}/sources/{citation_ref}"
    return TutorCitation(citationRef=citation_ref, documentVersion=document_version.version_number,
        textbookTitle=book.title, textbookEdition=book.edition, topicRef=topic.public_ref,
        topicCode=topic.code, topicTitle=topic.title, groupLabel=book.group_label,
        groupCode=group.code, groupTitle=group.title, contentKind=block.block_kind,
        passage=chunk.content, pdfPageIndex=page.page_number - 1, pdfPageNumber=page.page_number,
        printedPageLabel=str(label) if label else None,
        pageReference=f"printed page {label} (PDF page {page.page_number})" if label else f"PDF page {page.page_number}",
        boundingBox=chunk.bounding_box, confidence=round(max(0, min(1, confidence)), 6),
        assetRef=f"asset_{asset.id.hex}", sourceUrl=base, assetUrl=base + "/asset")


def _active_chunks(db: Session, session: TutorSession):
    topic = db.get(TextbookTopic, session.active_topic_id)
    version = _published_version(db, topic)
    if not version:
        return topic, None, None
    book = db.get(Textbook, topic.textbook_id)
    if topic.status != "published" or book.status != "published":
        return topic, None, None
    return topic, version, book


_SEARCH_STOP = frozenset('a an the this that these those is are was were be being been of in on at to from for with and or but it its by as me my i you your we our can could should would do does did have has had how why what which when where please explain describe show use using teach calculate about topic unit textbook source states matter so then than same also not only some very more less much many each any if just even always us them their there here such through rather out up down given take part answer ask short revision question questions tell write identify make necessarily exactly really completely'.split())


def _terms(text: str) -> set[str]:
    text = unicodedata.normalize('NFKC', text).lower()
    return {word for word in re.findall(r'[^\W_]+', text) if len(word) > 1 and word not in _SEARCH_STOP}


def _rank_evidence(query: str, records: list[tuple], approved_assets: set[str], threshold: float):
    """Combine lexical evidence with vectors; exact approved figure IDs win.

    Lexical fallback requires multiple discriminative terms, not an arbitrary
    lower vector threshold. Exercise prompts alone are not answer evidence.
    This score ranks evidence; it is not a measured probability of correctness.
    """
    wanted = _terms(query)
    requested_figures = set(re.findall(r'\bfig(?:ure)?\.?\s*(\d+(?:\.\d+)+)\b', query, re.I))
    documents = [_terms(chunk.content) for chunk, _, _ in records]
    frequency = Counter(term for terms in documents for term in terms)
    # Unknown phrasing must not dilute known evidence terms out of a long
    # student's question. Still require >=2 matching terms in the same passage.
    weights = {term: math.log(1 + len(records) / (1 + frequency[term]))
               for term in wanted if frequency[term]}
    total = sum(weights.values()) or 1
    ranked = []
    explicit_exercise = bool(re.search(r'\b(?:chapter\s+)?question\s+\d+', query, re.I))
    for (chunk, block, distance), terms in zip(records, documents):
        if not block or block.block_kind in {'heading', 'answer_space'}:
            continue
        if block.block_kind in {'question', 'subpart'} and not explicit_exercise:
            continue
        overlap = wanted & terms
        coverage = sum(weights[term] for term in overlap) / total
        lexical = min(.90, .45 + .45 * coverage) if len(overlap) >= 2 and coverage >= .25 else 0
        vector = max(0, 1 - float(distance))
        score = max(vector, lexical)
        figures = set(re.findall(r'\bfig(?:ure)?\.?\s*(\d+(?:\.\d+)+)\b', chunk.content, re.I))
        exact_visual = bool(requested_figures & figures and block.block_kind in {'diagram', 'image'}
                            and str(block.source_asset_id) in approved_assets)
        if requested_figures and block.block_kind in {'diagram', 'image'} and not exact_visual:
            continue
        if exact_visual:
            score = 1.0
        if score >= threshold:
            ranked.append((chunk, score, exact_visual))
    return sorted(ranked, key=lambda item: (-int(item[2]), -item[1], item[0].page_number, item[0].source_ordinal))


def search(db: Session, settings: Settings, principal: Principal, session_ref: str,
           query: str, edition: str | None, limit: int) -> TutorSourceSearchResponse:
    session = _session(db, settings, principal, session_ref)
    topic, version, book = _active_chunks(db, session)
    if not version or (edition and book.edition != edition):
        return TutorSourceSearchResponse(status="evidence_insufficient",
            message="No approved textbook topic is available.", query=query)
    vector = embed_texts(settings, [query])[0]
    distance = RetrievalChunk.embedding.cosine_distance(vector)
    rows = db.execute(select(RetrievalChunk, DocumentBlock, distance.label("distance")).join(
        DocumentBlock, DocumentBlock.id == RetrievalChunk.source_item_id).where(
        RetrievalChunk.status == "active", RetrievalChunk.source_type == "textbook_section",
        RetrievalChunk.topic_id == topic.id, RetrievalChunk.topic_content_version_id == version.id,
        DocumentBlock.needs_review.is_(False),
    ).order_by(distance, RetrievalChunk.page_number, RetrievalChunk.source_ordinal)).all()
    approved_assets = {item['documentAssetId'] for item in version.extraction_manifest.get('visualAssets', [])}
    ranked = _rank_evidence(query, rows, approved_assets, settings.tutor_retrieval_min_score)
    citations = []
    for chunk, confidence, _ in ranked:
        try:
            citations.append(_citation(db, session, chunk, confidence))
        except DomainError:
            continue
        if len(citations) >= limit:
            break
    return TutorSourceSearchResponse(status="exact" if citations else "evidence_insufficient",
        message="Exact approved topic evidence found." if citations else
            "AKURU could not find an exact approved passage in this topic. Do not invent a citation.",
        query=query, citations=citations)


def get_citation(db: Session, settings: Settings, principal: Principal, session_ref: str,
                 citation_ref: str) -> TutorCitation:
    session = _session(db, settings, principal, session_ref)
    topic, version, _ = _active_chunks(db, session)
    chunk = db.get(RetrievalChunk, _chunk_id(citation_ref))
    if not version or not chunk or chunk.status != "active" or chunk.topic_id != topic.id \
            or chunk.topic_content_version_id != version.id:
        raise DomainError("tutor_citation_not_found", "Citation not found.", 404)
    return _citation(db, session, chunk, 1)


def nearby_context(db: Session, settings: Settings, principal: Principal, session_ref: str,
                   citation_ref: str, radius: int) -> TutorCitationContextResponse:
    selected = get_citation(db, settings, principal, session_ref, citation_ref)
    session = tutor_sessions._owned_session(db, principal.user.id, session_ref)
    selected_chunk = db.get(RetrievalChunk, _chunk_id(citation_ref))
    chunks = db.scalars(select(RetrievalChunk).where(
        RetrievalChunk.status == "active", RetrievalChunk.source_type == "textbook_section",
        RetrievalChunk.topic_content_version_id == selected_chunk.topic_content_version_id,
        RetrievalChunk.document_version_id == selected_chunk.document_version_id,
        RetrievalChunk.topic_id == session.active_topic_id,
        RetrievalChunk.source_ordinal.between(max(0, selected_chunk.source_ordinal - radius),
                                               selected_chunk.source_ordinal + radius),
    ).order_by(RetrievalChunk.source_ordinal)).all()
    nearby = [get_citation(db, settings, principal, session_ref, f"citation_{chunk.id.hex}")
              for chunk in chunks if chunk.id != selected_chunk.id]
    return TutorCitationContextResponse(citation=selected, nearbyPassages=nearby,
        groundingInstruction="Explain only from these approved passages. Preserve each exact page reference and do not invent quotations.")


def open_asset(db: Session, settings: Settings, principal: Principal, storage: ObjectStorage,
               session_ref: str, citation_ref: str) -> StoredObject:
    citation = get_citation(db, settings, principal, session_ref, citation_ref)
    asset = db.get(DocumentAsset, uuid.UUID(hex=citation.assetRef.removeprefix("asset_")))
    try:
        return storage.get(asset.object_key, asset.mime_type)
    except FileNotFoundError as error:
        raise DomainError("tutor_citation_asset_missing", "The authorized citation image is unavailable.", 404) from error
