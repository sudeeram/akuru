"""Private Admin review state for source-grounded official questions."""
from datetime import datetime, timezone
import hashlib
import re
import uuid

import pymupdf

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.services import marking_rules
from app.errors import DomainError
from app.models import (
    AuditEvent, Document, DocumentAsset, DocumentBlock, DocumentPage, DocumentVersion,
    OfficialPaperReviewQuestion, OfficialPaperReviewWorkspace, RetrievalChunk, TextbookTopic,
    TextbookTopicContentVersion,
)
from app.schemas.official_paper_reviews import (
    CreateReviewCrop, PaperReviewResponse, ReviewCropResponse, ReviewEvidence, ReviewQuestionData, ReviewQuestionResponse,
    SaveReviewQuestion, SeedPaperReview, StartPaperReview,
)
from app.schemas.official_materials import (
    MarkSchemeEntryReview, MarkingPoint, OfficialQuestionReview,
    SaveOfficialMaterialReview, SourceLocation,
)
from app.security import Principal
from app.services import official_materials
from app.storage import ObjectStorage


def _paper(db: Session, paper_id: uuid.UUID) -> Document:
    paper = db.get(Document, paper_id)
    if not paper or paper.kind != "past_paper" or paper.removed_at:
        raise DomainError("past_paper_required", "Choose an available past paper.", 404)
    return paper


def _version(db: Session, document_id: uuid.UUID) -> DocumentVersion:
    version = db.scalar(select(DocumentVersion).where(
        DocumentVersion.document_id == document_id,
        DocumentVersion.status.in_(("needs_review", "completed")),
    ).order_by(DocumentVersion.version_number.desc()))
    if not version:
        raise DomainError("extraction_required", "Finish document extraction before starting review.", 409)
    return version


def _companion(db: Session, paper: Document, doc_id: uuid.UUID | None, kind: str):
    if not doc_id:
        return None, None
    doc = db.get(Document, doc_id)
    if not doc or doc.removed_at or doc.kind != kind or doc.source_document_id != paper.id:
        raise DomainError("invalid_companion", "Choose a matching paper companion.", 409)
    if (doc.course_id, doc.subject_id, doc.publication_year, doc.exam_session, doc.component, doc.variant) != (
        paper.course_id, paper.subject_id, paper.publication_year, paper.exam_session, paper.component, paper.variant
    ):
        raise DomainError("companion_identity_mismatch", "The companion's subject and exam identity must match the paper.", 409)
    return doc, _version(db, doc.id)


def _workspace(db: Session, paper_id: uuid.UUID) -> OfficialPaperReviewWorkspace:
    _paper(db, paper_id)
    workspace = db.scalar(select(OfficialPaperReviewWorkspace).where(
        OfficialPaperReviewWorkspace.paper_document_id == paper_id))
    if not workspace:
        raise DomainError("review_workspace_not_found", "Start the paper review first.", 404)
    return workspace


def _validate_bound_versions(db: Session, workspace: OfficialPaperReviewWorkspace) -> None:
    for document_id, version_id in (
        (workspace.paper_document_id, workspace.paper_version_id),
        (workspace.scheme_document_id, workspace.scheme_version_id),
        (workspace.report_document_id, workspace.report_version_id),
    ):
        if document_id and _version(db, document_id).id != version_id:
            raise DomainError("review_source_changed", "A source version changed. Start a new review after checking its evidence.", 409)


def _response(db: Session, workspace: OfficialPaperReviewWorkspace) -> PaperReviewResponse:
    rows = db.scalars(select(OfficialPaperReviewQuestion).where(
        OfficialPaperReviewQuestion.workspace_id == workspace.id
    ).order_by(OfficialPaperReviewQuestion.number)).all()
    questions = [ReviewQuestionResponse(
        number=row.number, revision=row.revision, status=row.status,
        data=ReviewQuestionData.model_validate(row.review_data),
        reviewedBy=str(row.reviewed_by) if row.reviewed_by else None,
        reviewedAt=row.reviewed_at.isoformat() if row.reviewed_at else None,
    ) for row in rows]
    approved = sum(row.status == "approved" for row in rows)
    blockers = []
    if not workspace.scheme_document_id:
        blockers.append("Attach the exact marking scheme.")
    if not workspace.expected_question_count or len(rows) != workspace.expected_question_count:
        blockers.append("Reconcile the complete question inventory.")
    if approved != len(rows):
        blockers.append(f"Approve {len(rows) - approved} remaining questions.")
    assessment_blockers = []
    for question in questions:
        for part in question.data.parts:
            if part.assessmentReadiness != "automatic":
                assessment_blockers.append(f"Q{question.number}({part.label}): automatic-marking rules are {part.assessmentReadiness.replace('_', ' ')}.")
        if all(p.assessmentReadiness == "automatic" for p in question.data.parts):
            try:
                marking_rules.compile_review(question.data)
            except DomainError as exc:
                assessment_blockers.append(f"Q{question.number}: {exc}")
    return PaperReviewResponse(
        paperDocumentId=str(workspace.paper_document_id), paperVersionId=str(workspace.paper_version_id),
        schemeDocumentId=str(workspace.scheme_document_id) if workspace.scheme_document_id else None,
        reportDocumentId=str(workspace.report_document_id) if workspace.report_document_id else None,
        expectedQuestionCount=workspace.expected_question_count, questionCount=len(rows),
        approvedCount=approved, wholePaperReady=not blockers, blockers=blockers, questions=questions,
        assessmentReleaseReady=not blockers and all((p.assessmentReadiness == "automatic" or (p.assessmentReadiness == "manual_only" and p.responseType == "drawing")) for q in questions for p in q.data.parts),
        automaticAssessmentReady=not blockers and not assessment_blockers, assessmentBlockers=assessment_blockers,
    )


def get(db: Session, paper_id: uuid.UUID) -> PaperReviewResponse:
    workspace = _workspace(db, paper_id)
    _validate_bound_versions(db, workspace)
    return _response(db, workspace)


def published_topic_evidence(db: Session, paper_id: uuid.UUID, topic_ref: str) -> dict:
    paper = _paper(db, paper_id)
    topic = db.scalar(select(TextbookTopic).where(TextbookTopic.public_ref == topic_ref,
        TextbookTopic.course_id == paper.course_id, TextbookTopic.subject_id == paper.subject_id,
        TextbookTopic.status == "published"))
    if not topic:
        raise DomainError("published_topic_not_found", "Choose a published topic in the paper's subject.", 404)
    rows = db.scalars(select(RetrievalChunk).where(
        RetrievalChunk.topic_id == topic.id, RetrievalChunk.status == "active",
        RetrievalChunk.source_type == "textbook_section"
    ).order_by(RetrievalChunk.page_number, RetrievalChunk.source_ordinal).limit(100)).all()
    return {"topicRef": topic.public_ref, "code": topic.code, "title": topic.title,
            "visualPages": visual_page_options(db, topic),
            "chunks": [{"pageNumber": row.page_number, "text": row.content} for row in rows]}


def visual_page_options(db: Session, topic: TextbookTopic) -> list[dict]:
    from app.services.student_textbooks import _visual_reference_sources
    content = db.scalar(select(TextbookTopicContentVersion).where(
        TextbookTopicContentVersion.topic_id == topic.id,
        TextbookTopicContentVersion.status == "published").order_by(
        TextbookTopicContentVersion.version_number.desc()))
    if not content:
        return []
    return [{"topicRef": topic.public_ref, "documentVersionId": str(version.id),
             "documentId": str(version.document_id), "page": page.page_number,
             "printedPageLabel": page.printed_page_label, "assetId": str(page.render_asset_id)}
            for _source, version, pages in _visual_reference_sources(db, content) for page in pages]


def validate_textbook_evidence(db: Session, paper: Document, part, previous_evidence: list | None = None) -> None:
    for evidence in part.textbookEvidence:
        topic = db.scalar(select(TextbookTopic).where(TextbookTopic.public_ref == evidence.topicRef))
        if (not topic or evidence.topicRef not in part.topicRefs
                or (topic.course_id, topic.subject_id) != (paper.course_id, paper.subject_id)):
            raise DomainError("invalid_textbook_evidence", "Textbook evidence must belong to a selected topic in this subject.", 422)
        # Historical publications remain valid provenance; current availability is shown separately.
        publications = db.scalars(select(TextbookTopicContentVersion).where(
            TextbookTopicContentVersion.topic_id == topic.id)).all()
        if not any(any(source.get("role") == "visual_reference" and
                       source.get("documentVersionId") == str(evidence.documentVersionId)
                       for source in publication.source_manifest) for publication in publications):
            raise DomainError("invalid_textbook_evidence", "Choose a published Visual reference source for this topic.", 422)
        page = db.scalar(select(DocumentPage).where(
            DocumentPage.document_version_id == evidence.documentVersionId,
            DocumentPage.page_number == evidence.page))
        historical = evidence.model_dump(mode="json") in (previous_evidence or [])
        if not page or (page.printed_page_label != evidence.printedPageLabel and not historical):
            raise DomainError("invalid_textbook_page", "Choose a reviewed printed-page label from this source version.", 422)


def published_topics(db: Session, paper_id: uuid.UUID) -> list[dict]:
    paper = _paper(db, paper_id)
    rows = db.scalars(select(TextbookTopic).where(
        TextbookTopic.course_id == paper.course_id, TextbookTopic.subject_id == paper.subject_id,
        TextbookTopic.status == "published").order_by(TextbookTopic.code)).all()
    return [{"topicRef": row.public_ref, "code": row.code, "title": row.title} for row in rows]


def create_review_crop(db: Session, storage: ObjectStorage, principal: Principal,
                       paper_id: uuid.UUID, payload: CreateReviewCrop) -> ReviewCropResponse:
    workspace = _workspace(db, paper_id)
    _validate_bound_versions(db, workspace)
    db.refresh(workspace, with_for_update=True)
    source_version_id = workspace.scheme_version_id if payload.source == "scheme" else workspace.paper_version_id
    if not source_version_id:
        raise DomainError("scheme_required", "Attach the matching marking scheme first.", 409)
    page = db.scalar(select(DocumentPage).where(
        DocumentPage.document_version_id == source_version_id,
        DocumentPage.page_number == payload.page,
    ))
    if not page:
        raise DomainError("invalid_source_page", "Choose a page in this question paper.", 422)
    if payload.x1 <= payload.x0 or payload.y1 <= payload.y0:
        raise DomainError("invalid_crop_bounds", "The crop must have a positive width and height.", 422)
    width, height = payload.x1 - payload.x0, payload.y1 - payload.y0
    if width < 0.02 or height < 0.02 or width * height > 0.65:
        raise DomainError("invalid_crop_size", "Select a focused diagram or table, not a tiny or near-full-page region.", 422)
    version = db.get(DocumentVersion, source_version_id)
    try:
        original = storage.get(version.object_key, version.mime_type)
        with pymupdf.open(stream=original.content, filetype="pdf") as pdf:
            source_page = pdf[payload.page - 1]
            rect = source_page.rect
            clip = pymupdf.Rect(rect.x0 + payload.x0 * rect.width, rect.y0 + payload.y0 * rect.height,
                                rect.x0 + payload.x1 * rect.width, rect.y0 + payload.y1 * rect.height)
            pixels_w, pixels_h = clip.width * 2.5, clip.height * 2.5  # 180 DPI
            if pixels_w > 4096 or pixels_h > 4096 or pixels_w * pixels_h > 12_000_000:
                raise DomainError("crop_render_limit", "Choose a smaller visual crop for this oversized PDF page.", 422)
            image = source_page.get_pixmap(dpi=180, alpha=False, clip=clip).tobytes("png")
    except (FileNotFoundError, IndexError, pymupdf.FileDataError) as exc:
        raise DomainError("source_render_unavailable", "The original paper page could not be rendered.", 409) from exc
    digest = hashlib.sha256(image).hexdigest()
    for existing in db.scalars(select(DocumentAsset).where(DocumentAsset.document_version_id == version.id, DocumentAsset.sha256 == digest)):
        metadata = existing.asset_metadata or {}
        if (metadata.get("altText") == payload.altText.strip() and metadata.get("answerVisual") == (payload.source == "scheme")
                and existing.page_number == payload.page and metadata.get("kind") == payload.kind
                and metadata.get("normalizedBounds") == {key: getattr(payload, key) for key in ("x0", "y0", "x1", "y1")}):
            return ReviewCropResponse(assetId=existing.id, page=payload.page, kind=payload.kind, altText=payload.altText.strip(), bounds=metadata["normalizedBounds"])
    asset_id = uuid.uuid4()
    key = f"derived/{version.id}/review-crops/{asset_id}.png"
    storage.put(key, image, "image/png")
    asset = DocumentAsset(id=asset_id, document_version_id=version.id,
        asset_kind=f"review_{payload.kind}_crop", object_key=key, mime_type="image/png",
        sha256=hashlib.sha256(image).hexdigest(), size_bytes=len(image), page_number=payload.page,
        bounding_box={"x0": clip.x0, "y0": clip.y0, "x1": clip.x1, "y1": clip.y1},
        asset_metadata={"answerVisual": payload.source == "scheme", "sourceSha256": version.sha256, "createdBy": str(principal.user.id), "reviewCrop": True, "reviewApproved": True, "kind": payload.kind, "altText": payload.altText.strip(),
                        "normalizedBounds": {key: getattr(payload, key) for key in ("x0", "y0", "x1", "y1")}})
    db.add(asset)
    db.add(AuditEvent(actor_id=principal.user.id, action="official_review.visual_cropped",
                      target_type="document", target_id=str(paper_id),
                      event_data={"assetId": str(asset_id), "page": payload.page, "kind": payload.kind, "source": payload.source}))
    db.commit()
    return ReviewCropResponse(assetId=asset_id, page=payload.page, kind=payload.kind, altText=payload.altText.strip(),
        bounds={key:getattr(payload,key) for key in ("x0","y0","x1","y1")})


def _candidate_boxes(page: pymupdf.Page) -> list[tuple[str, pymupdf.Rect]]:
    """Propose bounded visuals; reject PDF trim marks, borders and whole-page clusters."""
    bounds = page.rect
    tables = [pymupdf.Rect(table.bbox) for table in page.find_tables().tables]
    candidates: list[tuple[str, pymupdf.Rect]] = [("table", box) for box in tables]
    drawings = []
    for drawing in page.get_drawings():
        box = drawing["rect"]
        if (box.is_empty or box.width > bounds.width * .8 or box.height > bounds.height * .8
                or box.x0 < bounds.width * .04 or box.x1 > bounds.width * .96):
            continue
        if any((box & table).get_area() >= box.get_area() * .5 for table in tables):
            continue
        drawings.append(drawing)
    for region in page.cluster_drawings(drawings=drawings, x_tolerance=15, y_tolerance=15):
        box = pymupdf.Rect(region)
        if box.width < 40 or box.height < 35:
            continue
        if any((box & table).get_area() >= box.get_area() * .5 for table in tables):
            continue
        candidates.append(("diagram", box))
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") != 1:
            continue
        box = pymupdf.Rect(block["bbox"])
        if box.width >= 40 and box.height >= 35:
            candidates.append(("diagram", box))
    selected = []
    for kind, box in candidates:
        box = (box + (-6, -6, 6, 6)) & bounds
        if box.get_area() > bounds.get_area() * .65:
            continue
        if any(kind == prior_kind and (box & prior).get_area() > min(box.get_area(), prior.get_area()) * .8
               for prior_kind, prior in selected):
            continue
        selected.append((kind, box))
    return selected


def generate_review_candidates(db: Session, storage: ObjectStorage, principal: Principal,
                               paper_id: uuid.UUID) -> dict:
    workspace = _workspace(db, paper_id)
    _validate_bound_versions(db, workspace)
    version = db.get(DocumentVersion, workspace.paper_version_id)
    original = storage.get(version.object_key, version.mime_type)
    questions = db.scalars(select(OfficialPaperReviewQuestion).where(
        OfficialPaperReviewQuestion.workspace_id == workspace.id).order_by(OfficialPaperReviewQuestion.number)).all()
    pages_needed = {source["page"] for row in questions for source in row.review_data.get("paperSources", [])}
    created = 0
    attached = 0
    with pymupdf.open(stream=original.content, filetype="pdf") as pdf:
        candidates_by_page: dict[int, list[str]] = {}
        for page_number in sorted(pages_needed):
            page = pdf[page_number - 1]
            existing = db.scalars(select(DocumentAsset).where(
                DocumentAsset.document_version_id == version.id,
                DocumentAsset.page_number == page_number,
                DocumentAsset.asset_kind.in_(("candidate_diagram_crop", "candidate_table_crop")))).all()
            if existing:
                candidates_by_page[page_number] = [str(asset.id) for asset in existing]
                continue
            candidates_by_page[page_number] = []
            for kind, box in _candidate_boxes(page):
                if box.width * 2.5 > 4096 or box.height * 2.5 > 4096 or box.get_area() * 6.25 > 12_000_000:
                    continue
                image = page.get_pixmap(dpi=180, alpha=False, clip=box).tobytes("png")
                asset_id = uuid.uuid4()
                key = f"derived/{version.id}/review-candidates/{asset_id}.png"
                storage.put(key, image, "image/png")
                db.add(DocumentAsset(id=asset_id, document_version_id=version.id,
                    asset_kind=f"candidate_{kind}_crop", object_key=key, mime_type="image/png",
                    sha256=hashlib.sha256(image).hexdigest(), size_bytes=len(image), page_number=page_number,
                    bounding_box={"x0":box.x0,"y0":box.y0,"x1":box.x1,"y1":box.y1},
                    asset_metadata={"reviewCrop":True,"reviewApproved":False,"kind":kind,"altText":"",
                        "normalizedBounds":{"x0":box.x0/page.rect.width,"y0":box.y0/page.rect.height,
                                            "x1":box.x1/page.rect.width,"y1":box.y1/page.rect.height}}))
                candidates_by_page[page_number].append(str(asset_id))
                created += 1
    for row in questions:
        if row.status == "approved":
            continue
        data = dict(row.review_data)
        prior = list(data.get("candidateVisualAssetIds", []))
        assigned = set(data.get("visualAssetIds", [])) | {
            asset_id for part in data.get("parts", []) for asset_id in part.get("visualAssetIds", [])
        }
        proposed = list(dict.fromkeys([*prior, *(asset_id for source in data.get("paperSources", [])
            for asset_id in candidates_by_page.get(source["page"], []) if asset_id not in assigned)]))
        if proposed == prior:
            continue
        data["candidateVisualAssetIds"] = proposed
        row.review_data = data
        row.revision += 1
        attached += len(proposed) - len(prior)
    db.add(AuditEvent(actor_id=principal.user.id, action="official_review.visual_candidates_generated",
                      target_type="document", target_id=str(paper_id),
                      event_data={"created":created,"attached":attached}))
    db.commit()
    return {"created":created,"attached":attached,"questionCount":len(questions)}


def review_crops(db: Session, paper_id: uuid.UUID) -> list[ReviewCropResponse]:
    workspace = _workspace(db, paper_id)
    _validate_bound_versions(db, workspace)
    assets = db.scalars(select(DocumentAsset).where(
        DocumentAsset.document_version_id == workspace.paper_version_id,
        DocumentAsset.asset_kind.in_(("review_diagram_crop", "review_table_crop",
                                     "candidate_diagram_crop", "candidate_table_crop")),
    ).order_by(DocumentAsset.created_at)).all()
    return [ReviewCropResponse(assetId=asset.id, page=asset.page_number,
        kind=asset.asset_metadata["kind"], altText=asset.asset_metadata.get("altText", ""),
        approved=bool(asset.asset_metadata.get("reviewApproved")),
        bounds=asset.asset_metadata.get("normalizedBounds", {})) for asset in assets]


def start(db: Session, principal: Principal, paper_id: uuid.UUID, payload: StartPaperReview) -> PaperReviewResponse:
    paper = _paper(db, paper_id)
    version = _version(db, paper.id)
    scheme, scheme_version = _companion(db, paper, payload.schemeDocumentId, "mark_scheme")
    report, report_version = _companion(db, paper, payload.reportDocumentId, "examiner_report")
    workspace = db.scalar(select(OfficialPaperReviewWorkspace).where(
        OfficialPaperReviewWorkspace.paper_document_id == paper_id).with_for_update())
    if workspace:
        if workspace.paper_version_id != version.id:
            raise DomainError("review_source_changed", "The paper source changed. Preserve the old review before restarting.", 409)
        if any((workspace.scheme_document_id and scheme and workspace.scheme_document_id != scheme.id,
                workspace.report_document_id and report and workspace.report_document_id != report.id)):
            raise DomainError("review_companion_changed", "An attached companion cannot be silently replaced.", 409)
        if scheme and not workspace.scheme_document_id:
            workspace.scheme_document_id, workspace.scheme_version_id = scheme.id, scheme_version.id
        if report and not workspace.report_document_id:
            workspace.report_document_id, workspace.report_version_id = report.id, report_version.id
        if payload.expectedQuestionCount:
            count = db.scalar(select(func.count()).select_from(OfficialPaperReviewQuestion).where(
                OfficialPaperReviewQuestion.workspace_id == workspace.id)) or 0
            if count > payload.expectedQuestionCount:
                raise DomainError("inventory_mismatch", "Expected count is smaller than saved questions.", 409)
            workspace.expected_question_count = payload.expectedQuestionCount
    else:
        workspace = OfficialPaperReviewWorkspace(
            paper_document_id=paper.id, paper_version_id=version.id,
            scheme_document_id=scheme.id if scheme else None,
            scheme_version_id=scheme_version.id if scheme_version else None,
            report_document_id=report.id if report else None,
            report_version_id=report_version.id if report_version else None,
            expected_question_count=payload.expectedQuestionCount, created_by=principal.user.id,
        )
        db.add(workspace)
    db.add(AuditEvent(actor_id=principal.user.id, action="official_review.started", target_type="document",
                      target_id=str(paper.id), event_data={"expectedQuestionCount": workspace.expected_question_count}))
    db.commit()
    return _response(db, workspace)


def _validate_evidence(db: Session, version_id: uuid.UUID | None, sources, label: str):
    if sources and version_id is None:
        raise DomainError("companion_required", f"Attach the {label} source first.", 409)
    for source in sources:
        page = db.scalar(select(DocumentPage).where(
            DocumentPage.document_version_id == version_id,
            DocumentPage.page_number == source.page))
        if not page:
            raise DomainError("invalid_source_page", f"The {label} page does not belong to the selected source.", 422)
        if source.blockId and not db.scalar(select(DocumentBlock.id).where(
            DocumentBlock.id == source.blockId, DocumentBlock.document_version_id == version_id,
            DocumentBlock.page_id == page.id)):
            raise DomainError("invalid_source_block", f"The {label} block does not belong to that page.", 422)
        if source.assetId and not db.scalar(select(DocumentAsset.id).where(
            DocumentAsset.id == source.assetId, DocumentAsset.document_version_id == version_id,
            DocumentAsset.page_number == source.page)):
            raise DomainError("invalid_source_asset", f"The {label} visual does not belong to that page.", 422)


def _source_words(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.casefold())


def _matching_subpart_block(block: DocumentBlock, part) -> bool:
    if block.block_kind != "subpart" or block.needs_review:
        return False
    # OCR may include earlier answer space in the reviewed prompt, but the
    # candidate must contain the actual subpart wording and its label.
    block_words = _source_words(block.text)
    prompt_words = _source_words(part.prompt)
    label_words = _source_words(part.label)
    if len(block_words) < 5 or not label_words or not prompt_words:
        return False
    prefix = re.match(r"^\s*((?:\([a-zivx]+\)\s*)+)", block.text.casefold())
    if not prefix:
        return False
    block_label = re.findall(r"\(([a-zivx]+)\)", prefix.group(1))
    if block_label != label_words and not (len(label_words) > 1 and block_label == label_words[-1:]):
        return False
    return any(prompt_words[index:index + len(block_words)] == block_words
               for index in range(len(prompt_words) - len(block_words) + 1))


def _auto_link_exact_paper_blocks(db: Session, workspace: OfficialPaperReviewWorkspace,
                                  data: ReviewQuestionData) -> int:
    """Fill a missing exact paper citation only when one reviewed subpart block matches."""
    added = 0
    for part in data.parts:
        if part.status not in {"ready_for_approval", "approved"} or any(source.blockId for source in part.paperSources):
            continue
        page_numbers = {source.page for source in (part.paperSources or data.paperSources)}
        if not page_numbers:
            continue
        rows = db.execute(select(DocumentBlock, DocumentPage).join(
            DocumentPage, DocumentPage.id == DocumentBlock.page_id
        ).where(
            DocumentBlock.document_version_id == workspace.paper_version_id,
            DocumentPage.page_number.in_(page_numbers),
            DocumentBlock.block_kind == "subpart",
            DocumentBlock.needs_review.is_(False),
        )).all()
        matches = [(block, page) for block, page in rows if _matching_subpart_block(block, part)]
        if len(matches) != 1:
            continue
        block, page = matches[0]
        source = ReviewEvidence(page=page.page_number, blockId=block.id, assetId=page.render_asset_id)
        part.paperSources.append(source)
        added += 1
    if added:
        seen = {(source.page, source.blockId) for source in data.paperSources}
        for part in data.parts:
            for source in part.paperSources:
                key = (source.page, source.blockId)
                if source.blockId and key not in seen:
                    data.paperSources.append(source)
                    seen.add(key)
    return added


def _validate_question(db: Session, workspace: OfficialPaperReviewWorkspace,
                       status: str, data: ReviewQuestionData, previous_data: dict | None = None, question_number: str | None = None):
    _validate_evidence(db, workspace.paper_version_id, data.paperSources, "paper")
    for part in data.parts:
        previous_part = next((item for item in (previous_data or {}).get("parts", []) if item.get("label") == part.label), {})
        validate_textbook_evidence(db, _paper(db, workspace.paper_document_id), part, previous_part.get("textbookEvidence", []))
        from app.services.answer_visuals import validate_visuals
        validate_visuals(db, workspace.scheme_version_id, part.answerVisuals, {p.code for p in part.markingPoints}, part.label, question_number)
        if part.status in {"ready_for_approval", "approved"} and (part.answerVisualRequired or part.responseType == "drawing"):
            if not any(v.status == "approved" for v in part.answerVisuals) or any(v.status == "proposed" for v in part.answerVisuals):
                raise DomainError("answer_visual_review_required", f"Part {part.label}: approve the model-answer visuals or reject remaining proposals.", 409)
        if part.responseType == "drawing" and part.assessmentReadiness == "automatic":
            raise DomainError("drawing_manual_review_required", "Drawing assessment requires manual review until its evaluation gate passes. Select manual only.", 409)
        if part.assessmentReadiness == "automatic":
            marking_rules.validate_rules([p.model_dump() for p in part.markingPoints], part.marks, part.scoringRules.model_dump())
        if part.assessmentReadiness == "manual_only" and not part.assessmentReadinessReason.strip():
            raise DomainError("manual_marking_reason_required", f"Part {part.label}: explain why manual marking is required.", 422)
        _validate_evidence(db, workspace.paper_version_id, part.paperSources, "paper")
        _validate_evidence(db, workspace.scheme_version_id, part.schemeSources, "scheme")
        _validate_evidence(db, workspace.report_version_id, part.reportSources, "examiner report")
        if part.topicRefs:
            topics = db.scalars(select(TextbookTopic).where(TextbookTopic.public_ref.in_(part.topicRefs))).all()
            paper = db.get(Document, workspace.paper_document_id)
            if len(topics) != len(set(part.topicRefs)) or any(
                (topic.course_id, topic.subject_id, topic.status) != (paper.course_id, paper.subject_id, "published")
                for topic in topics
            ):
                raise DomainError("invalid_topic_mapping", "Choose only published topics in this paper's subject.", 422)
        if part.coverage == "supported" and not part.topicRefs:
            raise DomainError("topic_required", "A supported part needs a published topic.", 422)
        if part.coverage != "supported" and part.topicRefs:
            raise DomainError("unsupported_topic_mapping", "Only supported parts may have confirmed topic links.", 422)
        if part.status in {"ready_for_approval", "approved"}:
            missing = [name for name, valid in (
                ("wording", part.prompt.strip()), ("paper evidence", part.paperSources),
                ("scheme evidence", part.schemeSources), ("marking points", part.markingPoints),
                ("label", part.label.strip()), ("positive marks", part.marks > 0),
                ("coverage decision", part.coverage != "unreviewed"), ("coverage reason", part.coverage == "outside_current_coverage" or part.coverageReason.strip())) if not valid]
            if missing:
                raise DomainError("part_incomplete", f"Part {part.label}: complete {', '.join(missing)} before content approval.", 409)
            if not any(source.blockId for source in part.paperSources) or not any(source.blockId for source in part.schemeSources):
                raise DomainError("exact_block_required", "Link an exact question and scheme block before approval.", 409)
            if len({point.code for point in part.markingPoints}) != len(part.markingPoints):
                raise DomainError("duplicate_marking_code", "Marking-point codes must be unique per part.", 422)
            if any(not point.code.strip() or not point.text.strip() for point in part.markingPoints):
                raise DomainError("marking_point_incomplete", "Give every marking point a short code and wording before approval.", 422)
    assigned_ids = set(data.visualAssetIds) | {asset_id for part in data.parts for asset_id in part.visualAssetIds}
    visual_assets = []
    asset_by_id = {}
    for asset_id in assigned_ids | set(data.candidateVisualAssetIds):
        asset = db.scalar(select(DocumentAsset).where(
            DocumentAsset.id == asset_id, DocumentAsset.document_version_id == workspace.paper_version_id))
        if not asset:
            raise DomainError("invalid_question_asset", "The visual must come from this paper version.", 422)
        visual_assets.append(asset)
        asset_by_id[asset_id] = asset
    if status == "excluded":
        if not data.exclusionReason.strip():
            raise DomainError("exclusion_reason_required", "Explain why this source question is excluded.", 422)
    if status in {"ready_for_approval", "approved"}:
        if data.candidateVisualAssetIds:
            raise DomainError("unassigned_visual_candidates", "Assign or remove every candidate visual before approving the question.", 409)
        if not workspace.scheme_document_id or not data.paperSources or not data.prompt.strip() or data.marks <= 0:
            raise DomainError("question_incomplete", "Attach the scheme and review the complete question source.", 409)
        if sum(part.marks for part in data.parts) != data.marks:
            raise DomainError("question_marks_mismatch", "Subpart marks must add up to the question marks.", 422)
        required_part_status = "approved" if status == "approved" else "ready_for_approval"
        if any(part.status not in {required_part_status, "approved"} for part in data.parts):
            raise DomainError("parts_not_approved", "Approve every subpart first.", 409)
        if not any(source.blockId for source in data.paperSources):
            raise DomainError("exact_block_required", "Link an exact paper block before question approval.", 409)
        if any(not asset.asset_metadata.get("reviewApproved") for asset in visual_assets):
            raise DomainError("visual_review_required", "Review or replace every proposed visual before approving this question.", 409)
        if assigned_ids and not data.visualAltText.strip() and any(
            not asset.asset_metadata.get("altText", "").strip() for asset in visual_assets
        ):
            raise DomainError("visual_alt_required", "Describe approved visuals for accessibility.", 422)
        for part in data.parts:
            visible = set(data.visualAssetIds) | set(part.visualAssetIds)
            for keyword, kind in (("diagram", "diagram"), ("figure", "diagram"),
                                  ("graph", "diagram"), ("chromatogram", "diagram"), ("table", "table")):
                if keyword in part.prompt.casefold() and not any(
                    asset_by_id[asset_id].asset_metadata.get("kind") == kind
                    and asset_by_id[asset_id].asset_metadata.get("reviewCrop") for asset_id in visible
                ):
                    raise DomainError("required_part_visual_missing",
                        f"Attach a reviewed {kind} to part {part.label} before approving this question.", 409)


def _content_snapshot(data):
    value = ReviewQuestionData.model_validate(data).model_dump(mode="json")
    for part in value["parts"]:
        for field in ("scoringRules", "assessmentReadiness", "assessmentReadinessReason"):
            part.pop(field, None)
        for point in part["markingPoints"]:
            point.pop("acceptedAnswers", None)
    return value


def save_question(db: Session, principal: Principal, paper_id: uuid.UUID,
                  payload: SaveReviewQuestion) -> PaperReviewResponse:
    workspace = _workspace(db, paper_id)
    _validate_bound_versions(db, workspace)
    row = db.scalar(select(OfficialPaperReviewQuestion).where(
        OfficialPaperReviewQuestion.workspace_id == workspace.id,
        OfficialPaperReviewQuestion.number == payload.number).with_for_update())
    revision = row.revision if row else 0
    if revision != payload.expectedRevision:
        raise DomainError("review_conflict", "This question changed in another session. Reload before saving.", 409)
    auto_linked = _auto_link_exact_paper_blocks(db, workspace, payload.data)
    changed = bool(row and _content_snapshot(row.review_data) != _content_snapshot(payload.data.model_dump(mode="json")))
    if row and row.status == "approved" and payload.status == "approved" and changed:
        raise DomainError("reopen_required", "Reopen this approved question before editing it.", 409)
    if row and row.status == "approved" and payload.status != "approved":
        for part in payload.data.parts:
            if part.status == "approved":
                part.status = "needs_correction"
    _validate_question(db, workspace, payload.status, payload.data, row.review_data if row else None, payload.number)
    previous_textbook_evidence = [{"part": part.get("label"), "evidence": part.get("textbookEvidence", [])} for part in (row.review_data if row else {}).get("parts", [])]
    if row is None:
        row = OfficialPaperReviewQuestion(workspace_id=workspace.id, number=payload.number)
        db.add(row)
    else:
        row.revision += 1
    row.status = payload.status
    row.review_data = payload.data.model_dump(mode="json")
    row.reviewed_by = principal.user.id
    row.reviewed_at = datetime.now(timezone.utc)
    db.add(AuditEvent(actor_id=principal.user.id, action="official_review.question_saved",
                      target_type="document", target_id=str(paper_id),
                      event_data={"number": payload.number, "revision": row.revision, "status": row.status,
                                  "autoLinkedPaperBlocks": auto_linked,
                                  "previousTextbookEvidence": previous_textbook_evidence,
                                  "textbookEvidence": [{"part": part.label, "evidence": [item.model_dump(mode="json") for item in part.textbookEvidence]} for part in payload.data.parts]}))
    db.commit()
    return _response(db, workspace)


def seed(db: Session, principal: Principal, paper_id: uuid.UUID,
         payload: SeedPaperReview) -> PaperReviewResponse:
    workspace = _workspace(db, paper_id)
    _validate_bound_versions(db, workspace)
    if db.scalar(select(func.count()).select_from(OfficialPaperReviewQuestion).where(
        OfficialPaperReviewQuestion.workspace_id == workspace.id)):
        raise DomainError("review_already_started", "Import proposals only into an empty review workspace.", 409)
    bank = payload.draftBank
    paper = _paper(db, paper_id)
    paper_version = db.get(DocumentVersion, workspace.paper_version_id)
    if bank.get("status") != "local_draft_unreleased" or bank.get("studentAccess") is not False or bank.get("course") != paper.course_id or bank.get("subject") != paper.subject_id:
        raise DomainError("invalid_draft_bank", "Choose an unreleased bank for this subject.", 422)
    candidates = [item for item in bank.get("papers", []) if item.get("component") == paper.component]
    if len(candidates) != 1 or candidates[0].get("sourceSha256", {}).get("question") != paper_version.sha256:
        raise DomainError("source_hash_mismatch", "The draft bank question PDF does not match this uploaded paper.", 409)
    if workspace.scheme_version_id and candidates[0]["sourceSha256"].get("markScheme") != db.get(DocumentVersion, workspace.scheme_version_id).sha256:
        raise DomainError("source_hash_mismatch", "The marking scheme differs from the draft bank.", 409)
    if workspace.report_version_id and candidates[0]["sourceSha256"].get("examinerReport") != db.get(DocumentVersion, workspace.report_version_id).sha256:
        raise DomainError("source_hash_mismatch", "The examiner report differs from the draft bank.", 409)
    questions = [q for q in bank.get("questions", []) if q.get("paperKey") == candidates[0].get("paperKey")]
    if len(questions) != candidates[0].get("questionCount") or sum(q.get("marks", 0) for q in questions) != candidates[0].get("totalMarks"):
        raise DomainError("inventory_mismatch", "Draft question and mark totals do not reconcile.", 409)
    if workspace.expected_question_count and workspace.expected_question_count != len(questions):
        raise DomainError("inventory_mismatch", "Expected count differs from the draft bank.", 409)
    triage_rows = payload.coverageTriage.get("subparts", []) if payload.coverageTriage else []
    triage = {(r.get("component"), str(r.get("question")), r.get("subpart")): r for r in triage_rows}
    for q in questions:
        if q.get("studentPrompt") is not None or q.get("topicMappings"):
            raise DomainError("released_question_not_allowed", "Import only unreleased proposals.", 422)
        def sources(pages, version_id):
            if not version_id:
                return []
            out = []
            for number in pages:
                page = db.scalar(select(DocumentPage).where(
                    DocumentPage.document_version_id == version_id, DocumentPage.page_number == number))
                if not page:
                    raise DomainError("source_page_missing", f"Source page {number} is absent from the uploaded PDF.", 409)
                out.append({"page": number, "assetId": str(page.render_asset_id)})
            return out
        paper_sources = sources(q["source"]["questionPdfPages"], workspace.paper_version_id)
        scheme_sources = sources(q["source"]["schemePdfPages"], workspace.scheme_version_id)
        parts = []
        for part in q["subparts"]:
            suggestion = triage.get((q["component"], str(q["number"]), part["label"]), {})
            parts.append({
                "label": part["label"], "marks": part["marks"],
                "prompt": part.get("extractionCandidate", ""),
                "paperSources": paper_sources, "schemeSources": scheme_sources,
                "coverageReason": suggestion.get("reason", ""),
                "status": "unreviewed", "coverage": "unreviewed", "topicRefs": [],
            })
        data = ReviewQuestionData(
            marks=q["marks"], sharedStem=q.get("sharedStemExtractionCandidate", ""),
            prompt=q.get("rawQuestionExtraction", ""), paperSources=paper_sources,
            parts=parts,
        )
        db.add(OfficialPaperReviewQuestion(workspace_id=workspace.id,
            number=str(q["number"]), review_data=data.model_dump(mode="json")))
    workspace.expected_question_count = len(questions)
    db.add(AuditEvent(actor_id=principal.user.id, action="official_review.proposals_imported",
                      target_type="document", target_id=str(paper_id),
                      event_data={"questionCount": len(questions), "studentAccess": False}))
    db.commit()
    return _response(db, workspace)


def _exact_locations(db: Session, sources) -> list[SourceLocation]:
    locations = []
    seen = set()
    for source in sources:
        if not source.blockId or source.blockId in seen:
            continue
        block = db.get(DocumentBlock, source.blockId)
        locations.append(SourceLocation(page=source.page, blockId=block.id,
                                        boundingBox=block.bounding_box or {}))
        seen.add(source.blockId)
    return locations


def prepare_official_drafts(db: Session, principal: Principal, paper_id: uuid.UUID) -> dict:
    workspace = _workspace(db, paper_id)
    _validate_bound_versions(db, workspace)
    summary = _response(db, workspace)
    if not summary.wholePaperReady:
        raise DomainError("review_incomplete", "Finish the complete paper review before preparing official drafts.", 409)
    paper_questions = []
    scheme_entries = []
    for row in summary.questions:
        data = row.data
        if any(not (part.assessmentReadiness == "automatic" or (part.assessmentReadiness == "manual_only" and part.responseType == "drawing")) for part in data.parts):
            raise DomainError("assessment_rules_not_ready", f"Question {row.number}: content is approved, but every subpart needs an automatic or manual marking decision before preparing an assessment release.", 409)
        locations = _exact_locations(db, [*data.paperSources,
            *(source for part in data.parts for source in part.paperSources)])
        scheme_locations = _exact_locations(db, [source for part in data.parts for source in part.schemeSources])
        if not locations or not scheme_locations:
            raise DomainError("exact_block_required", "Every approved question needs exact paper and scheme blocks.", 409)
        assets = list(dict.fromkeys([*data.visualAssetIds,
            *(asset_id for part in data.parts for asset_id in part.visualAssetIds)]))
        paper_questions.append(OfficialQuestionReview(
            number=row.number, prompt=data.prompt, sharedStem=data.sharedStem,
            marks=data.marks, assetIds=assets,
            visualPlacements={"shared": data.visualAssetIds, **{
                part.label: part.visualAssetIds for part in data.parts if part.visualAssetIds}},
            sourceLocations=locations,
        ))
        compiled_points, rules = marking_rules.compile_review(data)
        points = [MarkingPoint.model_validate(p) for p in compiled_points]
        alternatives = [value for part in data.parts for value in part.alternatives]
        scheme_entries.append(MarkSchemeEntryReview(
            questionNumber=row.number, maxMarks=data.marks,
            markingPoints=points, scoringRules=rules, alternatives=alternatives, sourceLocations=scheme_locations,
            answerVisuals=[v.model_copy(update={"partLabel": part.label}) for part in data.parts for v in part.answerVisuals if v.status == "approved"],
            drawingParts=[part.label for part in data.parts if part.responseType == "drawing"],
        ))
    paper_payload = SaveOfficialMaterialReview(
        expectedItemCount=len(paper_questions), completenessConfirmed=True,
        questions=paper_questions,
    )
    scheme_payload = SaveOfficialMaterialReview(
        expectedItemCount=len(scheme_entries), completenessConfirmed=True,
        markSchemeEntries=scheme_entries,
    )
    paper_draft = official_materials.save_review(db, principal, paper_id, paper_payload)
    scheme_draft = official_materials.save_review(db, principal, workspace.scheme_document_id, scheme_payload)
    db.add(AuditEvent(actor_id=principal.user.id, action="official_review.drafts_prepared",
                      target_type="document", target_id=str(paper_id),
                      event_data={"questionCount": len(paper_questions), "schemeDocumentId": str(workspace.scheme_document_id)}))
    db.commit()
    return {"paperDocumentId": str(paper_id), "paperDraftVersion": paper_draft.versionNumber,
            "schemeDocumentId": str(workspace.scheme_document_id),
            "schemeDraftVersion": scheme_draft.versionNumber, "published": False}
