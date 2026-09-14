import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import DomainError
from app.models import (
    Document, DocumentAsset, DocumentBlock, DocumentPage, DocumentVersion, RetrievalChunk,
    TextbookContentVersion, TextbookUnit, TutorSession,
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
    require_tutor_access(db, settings, principal.user.id, TutorCapability.TOOLS)
    row = tutor_sessions._owned_session(db, principal.user.id, session_ref)
    if row.status != "active":
        raise DomainError("tutor_session_ended", "This tutor session has ended.", 409)
    coverage = curriculum_plans.student_coverage(db, principal.user.id, row.subject_id)
    if coverage.status != "ready" or str(row.active_unit_id) not in {item.id for item in coverage.coveredUnits}:
        raise DomainError("tutor_unit_not_eligible", "The active tutor unit is no longer eligible.", 409)
    return row


def _published_textbook(db: Session, session: TutorSession, edition: str | None = None):
    query = select(TextbookContentVersion, Document, DocumentVersion).join(
        Document, Document.id == TextbookContentVersion.document_id
    ).join(DocumentVersion, DocumentVersion.id == TextbookContentVersion.source_document_version_id).where(
        TextbookContentVersion.course_id == "igcse",
        TextbookContentVersion.subject_id == session.subject_id,
        TextbookContentVersion.status == "published",
        Document.review_state == "published", Document.removed_at.is_(None),
        DocumentVersion.status == "completed",
    )
    if edition:
        query = query.where(TextbookContentVersion.edition == edition)
    row = db.execute(query.order_by(TextbookContentVersion.published_at.desc(), TextbookContentVersion.version_number.desc())).first()
    if not row:
        return None
    version, document, document_version = row
    unit = db.get(TextbookUnit, session.active_unit_id)
    if not unit or unit.content_version_id != version.id or unit.subject_id != session.subject_id:
        return None
    return version, document, document_version, unit


def _asset(db: Session, chunk: RetrievalChunk, page: DocumentPage) -> DocumentAsset | None:
    asset_id = chunk.source_asset_id or page.render_asset_id
    asset = db.get(DocumentAsset, asset_id) if asset_id else None
    return asset if asset and asset.document_version_id == chunk.document_version_id else None


def _citation(db: Session, session: TutorSession, chunk: RetrievalChunk, document: Document,
              document_version: DocumentVersion, version: TextbookContentVersion,
              unit: TextbookUnit, page: DocumentPage, block: DocumentBlock,
              confidence: float) -> TutorCitation:
    asset = _asset(db, chunk, page)
    if not asset:
        raise DomainError("tutor_citation_asset_missing", "The authorized citation image is unavailable.", 409)
    citation_ref = f"citation_{chunk.id.hex}"
    label = page.printed_page_label or page.page_metadata.get("printedPageLabel")
    page_reference = f"printed page {label} (PDF page {page.page_number})" if label else f"PDF page {page.page_number}"
    source_base = f"/api/v1/tutoring/sessions/{session.public_ref}/sources/{citation_ref}"
    return TutorCitation(citationRef=citation_ref, documentVersion=document_version.version_number,
        textbookTitle=document.title, textbookEdition=version.edition, unitId=str(unit.id),
        unitCode=unit.unit_code, unitTitle=unit.title, contentKind=block.block_kind,
        passage=chunk.content, pdfPageIndex=page.page_number - 1, pdfPageNumber=page.page_number,
        printedPageLabel=str(label) if label else None, pageReference=page_reference,
        boundingBox=chunk.bounding_box, confidence=round(max(0, min(1, confidence)), 6),
        assetRef=f"asset_{asset.id.hex}", sourceUrl=source_base, assetUrl=source_base + "/asset")


def _exact_row(db: Session, session: TutorSession, chunk_id: uuid.UUID):
    textbook = _published_textbook(db, session)
    if not textbook:
        return None
    version, document, document_version, unit = textbook
    return db.execute(select(RetrievalChunk, DocumentPage, DocumentBlock).join(
        DocumentPage, (DocumentPage.document_version_id == RetrievalChunk.document_version_id) &
        (DocumentPage.page_number == RetrievalChunk.page_number)
    ).join(DocumentBlock, DocumentBlock.id == RetrievalChunk.source_item_id).where(
        RetrievalChunk.id == chunk_id, RetrievalChunk.status == "active",
        RetrievalChunk.source_type == "textbook_section", RetrievalChunk.course_id == "igcse",
        RetrievalChunk.subject_id == session.subject_id, RetrievalChunk.unit_id == session.active_unit_id,
        RetrievalChunk.textbook_content_version_id == version.id,
        RetrievalChunk.document_id == document.id,
        RetrievalChunk.document_version_id == document_version.id,
        DocumentBlock.needs_review.is_(False),
    )).first()


def search(db: Session, settings: Settings, principal: Principal, session_ref: str,
           query: str, edition: str | None, limit: int) -> TutorSourceSearchResponse:
    session = _session(db, settings, principal, session_ref)
    textbook = _published_textbook(db, session, edition)
    if not textbook:
        return TutorSourceSearchResponse(status="evidence_insufficient",
            message="No approved textbook edition is available for this eligible unit.", query=query)
    version, document, document_version, unit = textbook
    vector = embed_texts(settings, [query])[0]
    distance = RetrievalChunk.embedding.cosine_distance(vector)
    rows = db.execute(select(RetrievalChunk, DocumentPage, DocumentBlock, distance.label("distance")).join(
        DocumentPage, (DocumentPage.document_version_id == RetrievalChunk.document_version_id) &
        (DocumentPage.page_number == RetrievalChunk.page_number)
    ).join(DocumentBlock, DocumentBlock.id == RetrievalChunk.source_item_id).where(
        RetrievalChunk.status == "active", RetrievalChunk.source_type == "textbook_section",
        RetrievalChunk.course_id == "igcse", RetrievalChunk.subject_id == session.subject_id,
        RetrievalChunk.unit_id == session.active_unit_id,
        RetrievalChunk.textbook_content_version_id == version.id,
        RetrievalChunk.document_id == document.id,
        RetrievalChunk.document_version_id == document_version.id,
        DocumentBlock.needs_review.is_(False),
    ).order_by(distance, RetrievalChunk.page_number, RetrievalChunk.source_ordinal).limit(limit)).all()
    citations = []
    for chunk, page, block, raw_distance in rows:
        confidence = max(0.0, 1.0 - float(raw_distance))
        if confidence >= settings.tutor_retrieval_min_score:
            citations.append(_citation(db, session, chunk, document, document_version, version, unit, page, block, confidence))
    if not citations:
        return TutorSourceSearchResponse(status="evidence_insufficient",
            message="AKURU could not find an exact approved passage. Do not mention a textbook page or quotation.", query=query)
    return TutorSourceSearchResponse(status="exact", message="Exact approved textbook evidence found.",
                                     query=query, citations=citations)


def get_citation(db: Session, settings: Settings, principal: Principal, session_ref: str,
                 citation_ref: str) -> TutorCitation:
    session = _session(db, settings, principal, session_ref)
    row = _exact_row(db, session, _chunk_id(citation_ref))
    if not row:
        raise DomainError("tutor_citation_not_found", "Citation not found.", 404)
    chunk, page, block = row
    version, document, document_version, unit = _published_textbook(db, session)
    return _citation(db, session, chunk, document, document_version, version, unit, page, block, 1.0)


def nearby_context(db: Session, settings: Settings, principal: Principal, session_ref: str,
                   citation_ref: str, radius: int) -> TutorCitationContextResponse:
    selected = get_citation(db, settings, principal, session_ref, citation_ref)
    session = tutor_sessions._owned_session(db, principal.user.id, session_ref)
    selected_chunk = db.get(RetrievalChunk, _chunk_id(citation_ref))
    chunks = db.scalars(select(RetrievalChunk).where(
        RetrievalChunk.status == "active", RetrievalChunk.source_type == "textbook_section",
        RetrievalChunk.textbook_content_version_id == selected_chunk.textbook_content_version_id,
        RetrievalChunk.document_version_id == selected_chunk.document_version_id,
        RetrievalChunk.unit_id == session.active_unit_id,
        RetrievalChunk.source_ordinal.between(max(0, selected_chunk.source_ordinal - radius), selected_chunk.source_ordinal + radius),
    ).order_by(RetrievalChunk.source_ordinal)).all()
    nearby = [get_citation(db, settings, principal, session_ref, f"citation_{chunk.id.hex}")
              for chunk in chunks if chunk.id != selected_chunk.id]
    return TutorCitationContextResponse(citation=selected, nearbyPassages=nearby,
        groundingInstruction="Explain only from these approved passages. Preserve each exact page reference and do not invent quotations.")


def open_asset(db: Session, settings: Settings, principal: Principal, storage: ObjectStorage,
               session_ref: str, citation_ref: str) -> StoredObject:
    citation = get_citation(db, settings, principal, session_ref, citation_ref)
    asset_id = uuid.UUID(hex=citation.assetRef.removeprefix("asset_"))
    asset = db.get(DocumentAsset, asset_id)
    try:
        return storage.get(asset.object_key, asset.mime_type)
    except FileNotFoundError as error:
        raise DomainError("tutor_citation_asset_missing", "The authorized citation image is unavailable.", 404) from error
