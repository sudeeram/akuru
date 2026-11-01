"""Import AI-assisted source packages as unapproved documents, never publications."""
from __future__ import annotations

import hashlib
import io
import json
import stat
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import PurePosixPath

from PIL import Image
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.config import get_settings
from app.malware import scan
from app.models import Document, DocumentBlock, DocumentEvent, DocumentJob, DocumentPage, DocumentVersion, TextbookTopicDocument, TextbookTopicVisualAsset
from app.schemas.prepared_textbooks import PreparedPackage, PreparedReviewRequest
from app.security import Principal
from app.services import documents, textbook_structures
from app.services.document_processing import _store_asset
from app.storage.base import ObjectStorage

MAX_ARCHIVE = 50 * 1024 * 1024
MAX_EXPANDED = 100 * 1024 * 1024
METHOD = "prepared_visual_v1"


def invalid(message: str):
    raise DomainError("invalid_prepared_package", message, 422)


def _path(name: str) -> bool:
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and str(p) == name and ".." not in p.parts and "\\" not in name


def read_package(content: bytes) -> tuple[PreparedPackage, dict[str, bytes]]:
    if not content or len(content) > MAX_ARCHIVE:
        raise DomainError("prepared_package_too_large", "Choose a package no larger than 50 MB.", 413)
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > 401 or len({e.filename for e in entries}) != len(entries):
                invalid("The archive has duplicate names or too many files.")
            if any(not _path(e.filename) or e.is_dir() or e.flag_bits & 1 or stat.S_ISLNK(e.external_attr >> 16) for e in entries):
                invalid("Only ordinary, unencrypted relative files are accepted.")
            if sum(e.file_size for e in entries) > MAX_EXPANDED:
                invalid("The expanded package exceeds 100 MB.")
            manifest = archive.getinfo("topic-package.json")
            if manifest.file_size > 2 * 1024 * 1024:
                invalid("The package manifest exceeds 2 MB.")
            raw = archive.read(manifest)
            data = json.loads(raw, parse_constant=lambda _: invalid("Non-finite numbers are not accepted."))
            package = PreparedPackage.model_validate(data)
            paths = {p.sourcePath for p in package.pages} | {f.path for f in package.figures}
            if paths & {"topic-package.json"} or set(e.filename for e in entries) != paths | {"topic-package.json"}:
                invalid("Include exactly the manifest and its referenced PNG files.")
            if any(not _path(path) or not path.endswith('.png') for path in paths):
                invalid("Source pages and crops must be relative PNG files.")
            files = {path: archive.read(path) for path in paths}
    except (zipfile.BadZipFile, KeyError, ValueError, TypeError, RecursionError, RuntimeError, ValidationError) as exc:
        invalid("The archive or preparation manifest is invalid.")
    pages = {p.id: p for p in package.pages}
    if sum(p.width * p.height for p in package.pages) > 60_000_000:
        invalid("The package exceeds the 60-million-pixel source-page budget. Split it into smaller topic parts.")
    labels = {p.printedPage for p in package.pages}
    block_ids = {b.id for b in package.blocks}
    figure_ids = {f.id for f in package.figures}
    if (len(pages) != len(package.pages) or len(labels) != len(package.pages)
            or any(not label.isascii() or not label.isdecimal() for label in labels)
            or len(block_ids) != len(package.blocks) or len(figure_ids) != len(package.figures)
            or len({i.id for i in package.reviewIssues}) != len(package.reviewIssues)):
        invalid("Page labels must be unique positive integers; all record IDs must be unique.")
    numbers = {int(p.printedPage) for p in package.pages}
    if 0 in numbers:
        invalid("Printed page numbers must be positive.")
    for record in [*package.blocks, *package.figures, *package.exercises, *package.reviewIssues]:
        number = record.get('page') if isinstance(record, dict) else record.page
        if number not in numbers:
            invalid("Every content record must reference an included source page.")
    images = {}
    try:
        for p in package.pages:
            image = Image.open(io.BytesIO(files[p.sourcePath]))
            if image.format != 'PNG' or image.width * image.height > 20_000_000 or image.size != (p.width, p.height):
                invalid("Source image dimensions or format do not match the manifest.")
            image.load(); images[p.id] = image.convert('RGB')
        for record in [*package.pages, *package.figures]:
            path = record.sourcePath if hasattr(record, 'sourcePath') else record.path
            if hashlib.sha256(files[path]).hexdigest() != record.sha256:
                invalid("A source image or crop checksum does not match.")
        for f in package.figures:
            p = pages.get(f.pageId)
            if not p or int(p.printedPage) != f.page:
                invalid("Figure page identity does not match its source page.")
            x0, y0, x1, y1 = f.bboxPixels
            if not (0 <= x0 < x1 <= p.width and 0 <= y0 < y1 <= p.height):
                invalid("A figure crop is outside its source page.")
            crop = Image.open(io.BytesIO(files[f.path]))
            if crop.format != 'PNG' or crop.size != (x1-x0, y1-y0):
                invalid("Figure crop dimensions do not match its bounds.")
            if crop.convert('RGB').tobytes() != images[p.id].crop(f.bboxPixels).tobytes():
                invalid("Figure crops must retain the original source pixels.")
    except (OSError, Image.DecompressionBombError) as exc:
        invalid("A PNG source cannot be decoded safely.")
    for b in package.blocks:
        if not set(b.figureRefs) <= figure_ids:
            invalid("A teaching block references an unknown figure.")
        if b.kind == 'table' and (not b.columns or not b.rows or any(len(row) != len(b.columns) for row in b.rows)):
            invalid("Every table needs headers and equally sized rows, using null for missing cells.")
    for issue in package.reviewIssues:
        if not set(issue.blocks) <= block_ids:
            invalid("An exception references an unknown teaching block.")
    if len({ex.id for ex in package.exercises}) != len(package.exercises):
        invalid("Exercise IDs must be unique.")
    for exercise in package.exercises:
        if len({part.label for part in exercise.parts}) != len(exercise.parts):
            invalid("Exercise part labels must be unique within each question.")
        if any(not set(part.figureRefs) <= figure_ids for part in exercise.parts):
            invalid("Exercise parts need labels, wording and valid figure references.")
    return package, files


def preview(db: Session, book_ref: str, topic_ref: str, content: bytes) -> dict:
    book = textbook_structures._book(db, book_ref)
    topic = textbook_structures._topic(db, book, topic_ref)
    if topic.status == 'archived':
        raise DomainError('textbook_topic_archived', 'Restore the topic before importing a prepared draft.', 409)
    package, _ = read_package(content)
    if package.identity.get('course') != book.course_id or package.identity.get('subject') != book.subject_id:
        invalid("Package course and subject must match the selected textbook.")
    # Codes can differ (e.g. CHEM-U1-T01 versus 1); require the reviewed topic title.
    if ' '.join(str(package.identity.get('topicTitle', '')).lower().split()) != ' '.join(topic.title.lower().split()):
        invalid("Package topic title must match the selected destination topic.")
    return {"sha256": hashlib.sha256(content).hexdigest(), "topicRef": topic_ref,
            "title": package.identity['topicTitle'], "pageCount": len(package.pages),
            "blockCount": len(package.blocks), "figureCount": len(package.figures),
            "exerciseCount": len(package.exercises), "issues": [i.model_dump() for i in package.reviewIssues],
            "provenance": package.provenance, "role": "supporting", "published": False}


def import_package(db: Session, storage: ObjectStorage, principal: Principal, book_ref: str,
                   topic_ref: str, content: bytes) -> dict:
    summary = preview(db, book_ref, topic_ref, content)
    scan(content, get_settings())
    book = textbook_structures._book(db, book_ref)
    topic = textbook_structures._topic(db, book, topic_ref)
    # Serialize sequence assignment and repeated imports for this topic.
    db.refresh(topic, with_for_update=True)
    existing = db.scalar(select(Document).where(Document.sha256 == summary['sha256']))
    if existing:
        link = db.scalar(select(TextbookTopicDocument).where(TextbookTopicDocument.document_id == existing.id,
                                                          TextbookTopicDocument.topic_id == topic.id))
        if not link or existing.removed_at:
            raise DomainError("prepared_package_conflict", "This package was imported elsewhere or removed. Prepare a new candidate.", 409)
        return {**summary, "documentId": str(existing.id), "alreadyImported": True,
                "role": link.role, "published": existing.review_state == 'published'}
    package, files = read_package(content)
    doc_id, version_id = uuid.uuid4(), uuid.uuid4()
    key = f"prepared/{doc_id}/source.zip"
    stored = []
    class TrackedStorage:
        def put(self, object_key, data, mime):
            stored.append(object_key); storage.put(object_key, data, mime)
    writer = TrackedStorage()
    try:
        writer.put(key, content, 'application/zip')
        metadata = {"preparedPackage": package.model_dump(), "packageSha256": summary['sha256'],
                    "topicRef": topic_ref, "textbookRef": book_ref, "documentRole": "supporting"}
        document = Document(id=doc_id, kind='textbook', course_id=book.course_id, subject_id=book.subject_id,
            title=f"{topic.title} — prepared screenshot draft", original_filename='prepared-textbook.zip',
            object_key=key, mime_type='application/zip', sha256=summary['sha256'], size_bytes=len(content),
            uploaded_by=principal.user.id, source_metadata=metadata, review_state='pending', edition=book.edition)
        db.add(document); db.flush()
        version = DocumentVersion(id=version_id, document_id=doc_id, version_number=1,
            original_filename=document.original_filename, object_key=key, mime_type=document.mime_type,
            sha256=document.sha256, size_bytes=len(content), status='needs_review', uploaded_by=principal.user.id)
        db.add(version); db.flush()
        figures_by_page = {}
        for f in package.figures: figures_by_page.setdefault(f.page, []).append(f)
        for page_number, source in enumerate(package.pages, 1):
            asset = _store_asset(db, writer, version, METHOD, page_number, 1, 'page_render', 'image/png',
                                 files[source.sourcePath], None, {"preservedOriginal": True, "sourcePageId": source.id})
            page = DocumentPage(document_version_id=version_id, page_number=page_number,
                printed_page_label=source.printedPage, width_points=source.width, height_points=source.height,
                render_asset_id=asset.id, native_text='', extraction_method=METHOD, confidence=0,
                needs_review=True, page_metadata={"preparedSource": source.model_dump(), "confidenceNotMeasured": True})
            db.add(page); db.flush()
            sequence = 0
            def add_block(kind, text, metadata, latex=None, source_asset=None, bounds=None):
                nonlocal sequence
                if len(text) > 100_000:
                    invalid("Split content into reviewable blocks of no more than 100,000 characters.")
                sequence += 1
                row = DocumentBlock(document_version_id=version_id, page_id=page.id, sequence_number=sequence,
                    block_kind=kind, text=text, latex=latex, bounding_box=bounds or {"x0": 0, "y0": 0, "x1": 1, "y1": 1},
                    extraction_method=METHOD, confidence=0, needs_review=True, source_asset_id=source_asset,
                    block_metadata={"bboxSpace": "normalized", "preparedSource": metadata,
                                    "confidenceNotMeasured": True, "reconstruction": {"rawText": text}})
                db.add(row); db.flush(); return row
            printed = int(source.printedPage)
            for b in [b for b in package.blocks if b.page == printed]:
                text = '\n\n'.join(x for x in [b.title, b.text] if x)
                if b.items:
                    text += '\n\n' + '\n'.join(f'{index}. {item}' for index, item in enumerate(b.items, 1))
                if b.figureRefs:
                    text += '\n\nRelated source figures: ' + ', '.join(f'Figure {ref}' for ref in b.figureRefs) + '.'
                if b.kind == 'table':
                    text += '\n' + ' | '.join(b.columns) + '\n' + '\n'.join(' | '.join('—' if x is None else x for x in row) for row in b.rows)
                kind = b.kind if b.kind in {'heading', 'paragraph', 'table', 'equation'} else 'paragraph'
                add_block(kind, text, b.model_dump(), b.latex)
            for ex in [ex for ex in package.exercises if ex.page == printed]:
                text = ex.id + '. ' + ex.stem + '\n\n' + '\n\n'.join((part.label + ') ' if part.label else '') + part.prompt for part in ex.parts)
                if ex.wordBank:
                    text += '\n\nWord bank: ' + ', '.join(ex.wordBank)
                add_block('question', text, {"exercise": ex.model_dump()})
            for index, f in enumerate(figures_by_page.get(printed, []), 1):
                x0,y0,x1,y1 = f.bboxPixels
                bounds = {"x0": x0/source.width, "y0": y0/source.height, "x1": x1/source.width, "y1": y1/source.height}
                crop = _store_asset(db, writer, version, METHOD, page_number, index+1, 'diagram_crop',
                                    'image/png', files[f.path], bounds, {"figureId": f.id, "bboxSpace": "normalized"})
                caption = f"Figure {f.id}. {f.caption}"
                row = add_block('diagram', caption, f.model_dump(), source_asset=crop.id, bounds=bounds)
                row.block_metadata = {**row.block_metadata, "captionCandidate": caption, "altTextCandidate": f.altText}
                db.add(TextbookTopicVisualAsset(topic_id=topic.id, document_version_id=version_id,
                    document_asset_id=crop.id, block_id=row.id, status='selected', caption=caption,
                    alt_text=f.altText, selected_by=principal.user.id))
        db.add(DocumentJob(document_id=doc_id, document_version_id=version_id, stage=METHOD,
            status='needs_review', progress=100, attempt_count=1, extraction_version=METHOD,
            max_seconds=120, max_memory_mb=512, max_pages=100, completed_at=datetime.now(timezone.utc),
            result_data={"method": METHOD, "pageCount": len(package.pages), "provenance": package.provenance}))
        sequence = int(db.scalar(select(func.max(TextbookTopicDocument.sequence)).where(TextbookTopicDocument.topic_id == topic.id)) or 0)+1
        db.add(TextbookTopicDocument(topic_id=topic.id, document_version_id=version_id, document_id=doc_id,
            role='supporting', sequence=sequence, review_status='needs_review', created_by=principal.user.id,
            printed_start_page=package.pages[0].printedPage, printed_end_page=package.pages[-1].printedPage))
        db.add(DocumentEvent(document_id=doc_id, document_version_id=version_id, actor_id=principal.user.id,
            event_type='prepared_package_imported', event_data={"packageSha256": summary['sha256'], "topicRef": topic_ref}))
        textbook_structures._audit(db, principal, 'prepared_textbook.imported', 'document', str(doc_id),
                                   {"topicRef": topic_ref, "packageSha256": summary['sha256']})
        db.commit()
    except Exception:
        db.rollback()
        for object_key in reversed(stored):
            storage.delete(object_key)
        raise
    return {**summary, "documentId": str(doc_id), "alreadyImported": False}


def review_state(db: Session, book_ref: str, topic_ref: str, document_id: uuid.UUID) -> dict:
    book = textbook_structures._book(db, book_ref); topic = textbook_structures._topic(db, book, topic_ref)
    link = db.scalar(select(TextbookTopicDocument).where(TextbookTopicDocument.topic_id == topic.id,
                                                      TextbookTopicDocument.document_id == document_id))
    document = db.get(Document, document_id)
    if not link or not document or document.removed_at or not document.source_metadata.get('preparedPackage'):
        raise DomainError('prepared_package_not_found', 'The prepared draft could not be found in this topic.', 404)
    final = documents.final_document(db, document_id)
    return {"documentId": str(document_id), "contentHash": final.contentHash,
            "issues": document.source_metadata['preparedPackage'].get('reviewIssues', []),
            "decisions": document.source_metadata.get('preparedReview', {}).get('decisions', {}),
            "confirmed": final.confirmed, "immutable": document.review_state == 'published',
            "reviewUrl": f"/admin/textbooks/review/document_{document_id.hex}"}


def confirm_review(db: Session, principal: Principal, book_ref: str, topic_ref: str,
                   document_id: uuid.UUID, payload: PreparedReviewRequest) -> dict:
    state = review_state(db, book_ref, topic_ref, document_id)
    document = db.scalar(select(Document).where(Document.id == document_id).with_for_update())
    if document.review_state == 'published':
        raise DomainError('published_document_immutable', 'Create a review revision before editing published content.', 409)
    # Re-read after acquiring the lock; existing block edits change this digest.
    if documents.final_document(db, document_id).contentHash != payload.contentHash:
        raise DomainError('prepared_review_stale', 'The draft changed. Reload and review it again before confirming.', 409)
    ids = {i['id'] for i in state['issues']}
    if not payload.confirmWholeDocument or set(payload.decisions) != ids or any(not note.strip() or len(note) > 5000 for note in payload.decisions.values()):
        raise DomainError('prepared_review_incomplete', 'Review the whole document and record a resolution for every exception.', 422)
    _, version = documents.get_document(db, document_id)
    now = datetime.now(timezone.utc).isoformat()
    blocks = db.scalars(select(DocumentBlock).where(DocumentBlock.document_version_id == version.id)).all()
    for block in blocks:
        source_id = block.block_metadata.get('preparedSource', {}).get('id')
        notes = [payload.decisions[i['id']].strip() for i in state['issues'] if source_id in i['blocks']]
        # Notes are evidence presented to the learner/model, not hidden metadata.
        if notes:
            original = block.text
            old_suffix = block.block_metadata.get('preparedReviewSuffix', '')
            if old_suffix and original.endswith(old_suffix):
                original = original[:-len(old_suffix)]
            suffix = '\n\nReviewed teaching clarification: ' + '\n'.join(notes)
            block.text = original + suffix
            block.block_metadata = {**block.block_metadata, "preparedReviewSuffix": suffix}
            scientific = block.block_metadata.get('scientificContent')
            if scientific:
                alias = scientific.get('plainText', original)
                if old_suffix and alias.endswith(old_suffix):
                    alias = alias[:-len(old_suffix)]
                block.block_metadata = {**block.block_metadata, "scientificContent": {
                    **scientific, "text": block.text, "plainText": alias + suffix,
                    "marks": [mark for mark in scientific.get('marks', []) if mark['end'] <= len(original)]},
                    "searchAlias": alias + suffix}
        block.needs_review = False
        block.block_metadata = {**block.block_metadata, "adminReviewed": True, "reviewedBy": str(principal.user.id)}
    for page in db.scalars(select(DocumentPage).where(DocumentPage.document_version_id == version.id)).all():
        if not page.printed_page_label:
            raise DomainError('prepared_page_label_missing', 'Save a printed page label on every page.', 409)
        page.needs_review = False
        page.page_metadata = {**page.page_metadata, "adminReviewed": True, "printedPageLabelConfirmed": True, "reviewedBy": str(principal.user.id)}
    document.source_metadata = {**document.source_metadata, "preparedReview": {"decisions": payload.decisions,
        "reviewedBy": str(principal.user.id), "reviewedAt": now}}
    for job in db.scalars(select(DocumentJob).where(DocumentJob.document_version_id == version.id,
                                                   DocumentJob.stage == METHOD)).all():
        job.status = 'completed'
    db.add(DocumentEvent(document_id=document.id, document_version_id=version.id, actor_id=principal.user.id,
        event_type='prepared_package_reviewed', event_data={"decisions": payload.decisions, "inputContentHash": payload.contentHash}))
    db.flush()
    documents._refresh_topic_document_readiness(db, version.id, principal.user.id)
    # Existing final confirmation checks and hash remain authoritative.
    documents.confirm_final_document(db, principal, document_id, confirm_complete=True)
    return review_state(db, book_ref, topic_ref, document_id)
