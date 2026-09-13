import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import (
    Document, DocumentEvent, DocumentPage, TextbookContentVersion, TextbookUnit, TextbookUnitVersion,
)
from app.schemas.textbooks import SaveTextbookReviewRequest, TextbookReviewResponse, TextbookUnitDraft
from app.security import Principal, utcnow
from app.services.documents import get_document


def _textbook(db: Session, document_id: uuid.UUID):
    document, source_version = get_document(db, document_id)
    if document.kind != "textbook":
        raise DomainError("textbook_required", "Choose a textbook document.", 422)
    if source_version.status not in {"needs_review", "completed"}:
        raise DomainError("textbook_extraction_incomplete", "Complete document extraction before reviewing units.", 409)
    return document, source_version


def _current(db: Session, document_id: uuid.UUID):
    return db.scalar(select(TextbookContentVersion).where(
        TextbookContentVersion.document_id == document_id,
        TextbookContentVersion.status.in_(("draft", "published")),
    ).order_by(TextbookContentVersion.version_number.desc()))


def response(db: Session, version: TextbookContentVersion) -> TextbookReviewResponse:
    rows = db.scalars(select(TextbookUnitVersion).where(
        TextbookUnitVersion.content_version_id == version.id
    ).order_by(TextbookUnitVersion.sequence)).all()
    return TextbookReviewResponse(
        versionNumber=version.version_number, status=version.status, courseId=version.course_id,
        subjectId=version.subject_id, edition=version.edition,
        units=[TextbookUnitDraft(
            code=row.unit_code, chapter=row.chapter, title=row.title, summary=row.summary,
            startPage=row.start_page, endPage=row.end_page, sections=row.sections,
            definitions=row.definitions, concepts=row.concepts, equations=row.equations,
            examples=row.examples, diagrams=row.diagrams,
        ) for row in rows],
    )


def get_review(db: Session, document_id: uuid.UUID) -> TextbookReviewResponse:
    _textbook(db, document_id)
    version = _current(db, document_id)
    if not version:
        raise DomainError("textbook_review_not_found", "No textbook unit review has been saved yet.", 404)
    return response(db, version)


def propose_review(db: Session, principal: Principal, document_id: uuid.UUID):
    document, source_version = _textbook(db, document_id)
    pages = db.scalars(select(DocumentPage).where(
        DocumentPage.document_version_id == source_version.id
    ).order_by(DocumentPage.page_number)).all()
    from app.models import DocumentBlock
    blocks = db.scalars(select(DocumentBlock).where(
        DocumentBlock.document_version_id == source_version.id
    ).order_by(DocumentBlock.page_id, DocumentBlock.sequence_number)).all()
    page_number = {page.id: page.page_number for page in pages}
    headings = [block for block in blocks if block.block_kind == "heading" and block.text.strip()]
    if not headings:
        headings = [next((block for block in blocks if block.text.strip()), None)]
    headings = [heading for heading in headings if heading][:50]
    if not headings:
        raise DomainError("textbook_content_missing", "No extracted textbook text is available to propose units.", 409)
    units = []
    last_page = pages[-1].page_number if pages else 1
    for index, heading in enumerate(headings):
        start = page_number.get(heading.page_id, 1)
        end = (page_number.get(headings[index + 1].page_id, last_page + 1) - 1) if index + 1 < len(headings) else last_page
        scoped = [block for block in blocks if start <= page_number.get(block.page_id, 0) <= max(start, end)]
        text = [block.text.strip() for block in scoped if block.text.strip()]
        units.append(TextbookUnitDraft(
            code=f"U{index + 1}", chapter=f"Chapter {index + 1}", title=heading.text.strip()[:240],
            summary=" ".join(text[:3])[:5000], startPage=start, endPage=max(start, end),
            sections=[block.text.strip() for block in scoped if block.block_kind == "heading" and block.text.strip()][:100],
            definitions=[value for value in text if " is " in value.lower()][:100],
            concepts=text[:20],
            equations=[block.latex or block.text for block in scoped if block.block_kind == "equation" and (block.latex or block.text)][:100],
            examples=[value for value in text if "example" in value.lower()][:100],
            diagrams=[f"Page {page_number.get(block.page_id)} diagram" for block in scoped if block.block_kind in {"diagram", "image"}][:100],
        ))
    return save_review(db, principal, document_id, SaveTextbookReviewRequest(
        courseId=document.course_id, subjectId=document.subject_id,
        edition=document.edition or "Unspecified", units=units,
    ))


def save_review(db: Session, principal: Principal, document_id: uuid.UUID, payload: SaveTextbookReviewRequest):
    document, source_version = _textbook(db, document_id)
    if (payload.courseId, payload.subjectId) != (document.course_id, document.subject_id):
        raise DomainError("textbook_scope_mismatch", "Confirm the textbook's existing course and subject.", 422)
    if document.edition and payload.edition != document.edition:
        raise DomainError("textbook_edition_mismatch", "Confirm the edition entered when the textbook was uploaded.", 422)
    codes = [unit.code.lower() for unit in payload.units]
    if len(codes) != len(set(codes)):
        raise DomainError("duplicate_unit_code", "Unit codes must be unique within the textbook.", 409)
    page_count = db.scalar(select(func.count()).select_from(DocumentPage).where(
        DocumentPage.document_version_id == source_version.id
    )) or 0
    if any(unit.endPage > page_count for unit in payload.units):
        raise DomainError("unit_page_out_of_range", "A unit page range is outside the extracted textbook.", 422)
    current = _current(db, document_id)
    if current and current.status == "published":
        version_number = current.version_number + 1
        current = None
    else:
        version_number = current.version_number if current else 1
    version = current or TextbookContentVersion(
        document_id=document.id, source_document_version_id=source_version.id,
        version_number=version_number, course_id=document.course_id, subject_id=document.subject_id,
        edition=payload.edition, created_by=principal.user.id, status="draft",
    )
    db.add(version); db.flush()
    db.execute(delete(TextbookUnitVersion).where(TextbookUnitVersion.content_version_id == version.id))
    for sequence, unit in enumerate(payload.units, 1):
        db.add(TextbookUnitVersion(
            content_version_id=version.id, unit_code=unit.code, chapter=unit.chapter, title=unit.title,
            summary=unit.summary, sequence=sequence, start_page=unit.startPage,
            end_page=unit.endPage, sections=unit.sections, definitions=unit.definitions,
            concepts=unit.concepts, equations=unit.equations, examples=unit.examples,
            diagrams=unit.diagrams,
        ))
    db.add(DocumentEvent(document_id=document.id, document_version_id=source_version.id,
        actor_id=principal.user.id, event_type="textbook_review_saved",
        event_data={"contentVersion": version_number, "unitCount": len(payload.units)}))
    db.commit(); db.refresh(version)
    return response(db, version)


def publish(db: Session, principal: Principal, document_id: uuid.UUID, confirmations):
    document, source_version = _textbook(db, document_id)
    if not all((confirmations.confirmCourse, confirmations.confirmSubject, confirmations.confirmEdition)):
        raise DomainError("textbook_confirmation_required", "Confirm course, subject and edition before publishing.", 422)
    version = _current(db, document_id)
    if not version or version.status != "draft":
        raise DomainError("textbook_draft_required", "Save a textbook review draft before publishing.", 409)
    rows = db.scalars(select(TextbookUnitVersion).where(TextbookUnitVersion.content_version_id == version.id).order_by(TextbookUnitVersion.sequence)).all()
    if not rows:
        raise DomainError("textbook_units_required", "Add at least one reviewed unit before publishing.", 409)
    previous = db.scalars(select(TextbookContentVersion).where(
        TextbookContentVersion.document_id == document.id,
        TextbookContentVersion.status == "published",
    ).with_for_update()).all()
    now = utcnow()
    for old in previous:
        old.status = "superseded"; old.superseded_at = now
    version.status = "published"; version.published_by = principal.user.id; version.published_at = now
    document.review_state = "published"
    for row in rows:
        db.add(TextbookUnit(
            textbook_id=document.id, course_id=document.course_id, subject_id=document.subject_id,
            unit_code=row.unit_code, title=row.title, sequence=row.sequence,
            content_version_id=version.id,
        ))
    db.add(DocumentEvent(document_id=document.id, document_version_id=source_version.id,
        actor_id=principal.user.id, event_type="textbook_published",
        event_data={"contentVersion": version.version_number, "unitCount": len(rows)}))
    db.commit(); db.refresh(version)
    return response(db, version)
