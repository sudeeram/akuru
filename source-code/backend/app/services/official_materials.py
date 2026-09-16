import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import (
    AuditEvent, Document, DocumentAsset, DocumentBlock, DocumentPage, DocumentVersion,
    ExaminerCommentVersion, MarkSchemeEntryVersion, OfficialMaterialVersion,
    OfficialQuestionVersion, Textbook,
    TextbookContentVersion,
)
from app.schemas.official_materials import (
    ExaminerCommentReview, MarkSchemeEntryReview, MarkingPoint, OfficialMaterialReview,
    OfficialQuestionReview, SaveOfficialMaterialReview, SourceLocation,
)
from app.security import Principal


NUMBER_RE = re.compile(r"^\s*(?:question\s+)?(\d+(?:\s*\([a-z0-9ivx]+\))*)[.)]?\s*", re.I)
MARK_RE = re.compile(r"\[(\d+)\]\s*$")
MARKING_CODE_RE = re.compile(r"^\s*([MABC]\d+)\s*[:.\-]?\s*", re.I)
ADVICE_RE = re.compile(r"\b(?:should|need(?:ed)? to|recommend(?:ed)?|advice|improve by)\b", re.I)


def _document(db: Session, document_id: uuid.UUID) -> Document:
    document = db.get(Document, document_id)
    if not document or document.removed_at is not None:
        raise DomainError("document_not_found", "Document not found.", 404)
    if document.kind not in {"past_paper", "mark_scheme", "examiner_report"}:
        raise DomainError("official_material_required", "Choose a past paper, marking scheme or examiner report.", 422)
    return document


def _source_version(db: Session, document_id: uuid.UUID) -> DocumentVersion:
    version = db.scalar(select(DocumentVersion).where(
        DocumentVersion.document_id == document_id,
        DocumentVersion.status.in_(("needs_review", "completed")),
    ).order_by(DocumentVersion.version_number.desc()))
    if not version:
        raise DomainError("extraction_required", "Complete deterministic extraction before reviewing this document.", 409)
    return version


def _current(db: Session, document_id: uuid.UUID):
    return db.scalar(select(OfficialMaterialVersion).where(
        OfficialMaterialVersion.document_id == document_id,
        OfficialMaterialVersion.status.in_(("draft", "published")),
    ).order_by(OfficialMaterialVersion.version_number.desc()))


def _published_textbook_version(db: Session, document: Document):
    version = db.scalar(select(TextbookContentVersion).where(
        TextbookContentVersion.course_id == document.course_id,
        TextbookContentVersion.subject_id == document.subject_id,
        TextbookContentVersion.status == "published",
    ).order_by(TextbookContentVersion.published_at.desc()))
    if not version:
        raise DomainError("published_textbook_required", "Publish a same-subject textbook before reviewing this paper.", 409)
    return version


def _published_textbook(db: Session, document: Document):
    return db.scalar(select(Textbook).where(
        Textbook.course_id == document.course_id, Textbook.subject_id == document.subject_id,
        Textbook.status == "published",
    ).order_by(Textbook.published_at.desc()))


def _locations(block: DocumentBlock, page_number: int) -> list[SourceLocation]:
    return [SourceLocation(page=page_number, blockId=str(block.id), boundingBox=block.bounding_box)]


def _proposal_rows(db: Session, version: DocumentVersion, kind: str):
    rows = db.execute(select(DocumentBlock, DocumentPage.page_number, DocumentPage.render_asset_id).join(
        DocumentPage, DocumentPage.id == DocumentBlock.page_id
    ).where(DocumentBlock.document_version_id == version.id).order_by(
        DocumentPage.page_number, DocumentBlock.sequence_number
    )).all()
    candidates = [(block, page) for block, page, _ in rows if block.block_kind in {"question", "subpart"}]
    if not candidates:
        candidates = [(block, page) for block, page, _ in rows if block.text.strip()]
    if kind == "past_paper":
        starts = [index for index, (block, _, _) in enumerate(rows) if block.block_kind in {"question", "subpart"}]
        if not starts:
            starts = [index for index, (block, _, _) in enumerate(rows) if block.text.strip()]
        preamble = "\n".join(block.text.strip() for block, _, _ in rows[:starts[0]] if block.text.strip()) if starts else ""
        questions = []
        for position, start in enumerate(starts):
            end = starts[position + 1] if position + 1 < len(starts) else len(rows)
            group = rows[start:end]
            first_text = group[0][0].text.strip()
            match = NUMBER_RE.match(first_text)
            number = match.group(1).replace(" ", "") if match else str(position + 1)
            texts = [(first_text[match.end():].strip() if match else first_text)]
            texts.extend(block.text.strip() for block, _, _ in group[1:] if block.text.strip())
            prompt = "\n".join(value for value in texts if value)
            mark_match = MARK_RE.search(prompt)
            marks = int(mark_match.group(1)) if mark_match else 1
            if mark_match:
                prompt = (prompt[:mark_match.start()] + prompt[mark_match.end():]).strip()
            questions.append(OfficialQuestionReview(
                number=number, parentNumber=number.split("(", 1)[0] if "(" in number else None,
                prompt=prompt or f"Question {number}", sharedStem=preamble, marks=marks,
                equations=[block.latex for block, _, _ in group if block.latex],
                assetIds=list(dict.fromkeys([
                    asset_id for block, _, render_asset_id in group
                    for asset_id in (render_asset_id, block.source_asset_id) if asset_id
                ])),
                sourceLocations=[location for block, page, _ in group for location in _locations(block, page)],
            ))
        return questions
    proposed = []
    for index, (block, page) in enumerate(candidates, 1):
        text = block.text.strip()
        match = NUMBER_RE.match(text)
        number = match.group(1).replace(" ", "") if match else str(index)
        prompt = text[match.end():].strip() if match else text
        mark_match = MARK_RE.search(prompt)
        marks = int(mark_match.group(1)) if mark_match else 1
        if mark_match:
            prompt = prompt[:mark_match.start()].strip()
        location = _locations(block, page)
        if kind == "mark_scheme":
            code_match = MARKING_CODE_RE.match(prompt)
            code = code_match.group(1).upper() if code_match else f"P{index}"
            point_text = prompt[code_match.end():].strip() if code_match else (prompt or text)
            point_kind = {"M": "method", "A": "accuracy", "B": "independent", "C": "communication"}.get(code[0], "other")
            alternatives = [value.strip() for value in re.split(r"\s+(?:or|accept|allow)\s+", point_text, flags=re.I)[1:] if value.strip()]
            proposed.append(MarkSchemeEntryReview(
                questionNumber=number, maxMarks=marks,
                markingPoints=[MarkingPoint(code=code, text=point_text, kind=point_kind)],
                alternatives=alternatives,
                sourceLocations=location,
            ))
        else:
            is_advice = bool(ADVICE_RE.search(prompt or text))
            proposed.append(ExaminerCommentReview(
                questionNumber=number,
                commonMistakes=[] if is_advice else [prompt or text],
                advice=[prompt or text] if is_advice else [], sourceLocations=location,
            ))
    return proposed


def _response(db: Session, material: OfficialMaterialVersion) -> OfficialMaterialReview:
    questions = db.scalars(select(OfficialQuestionVersion).where(OfficialQuestionVersion.material_version_id == material.id).order_by(OfficialQuestionVersion.question_number)).all()
    schemes = db.scalars(select(MarkSchemeEntryVersion).where(MarkSchemeEntryVersion.material_version_id == material.id).order_by(MarkSchemeEntryVersion.question_number)).all()
    comments = db.scalars(select(ExaminerCommentVersion).where(ExaminerCommentVersion.material_version_id == material.id).order_by(ExaminerCommentVersion.question_number)).all()
    return OfficialMaterialReview(
        versionNumber=material.version_number, status=material.status, kind=material.kind,
        courseId=material.course_id, subjectId=material.subject_id,
        sourcePaperId=str(material.source_paper_id) if material.source_paper_id else None,
        sourcePaperVersionId=str(material.source_paper_version_id) if material.source_paper_version_id else None,
        expectedItemCount=material.inventory_count, completenessConfirmed=material.completeness_confirmed,
        questions=[OfficialQuestionReview(number=q.question_number, parentNumber=q.parent_number, prompt=q.prompt, sharedStem=q.shared_stem, marks=q.marks, equations=q.equations, assetIds=q.asset_ids, sourceLocations=q.source_locations) for q in questions],
        markSchemeEntries=[MarkSchemeEntryReview(questionNumber=e.question_number, maxMarks=e.max_marks, markingPoints=e.marking_points, alternatives=e.alternatives, sourceLocations=e.source_locations) for e in schemes],
        examinerComments=[ExaminerCommentReview(questionNumber=c.question_number, commonMistakes=c.common_mistakes, advice=c.advice, sourceLocations=c.source_locations) for c in comments],
    )


def get_review(db: Session, document_id: uuid.UUID):
    document = _document(db, document_id)
    material = _current(db, document.id)
    if not material:
        raise DomainError("official_review_not_found", "Create an extraction proposal first.", 404)
    return _response(db, material)


def propose_review(db: Session, principal: Principal, document_id: uuid.UUID):
    document = _document(db, document_id)
    version = _source_version(db, document.id)
    current = _current(db, document.id)
    if current and current.status == "draft":
        return _response(db, current)
    next_version = (db.scalar(select(func.max(OfficialMaterialVersion.version_number)).where(OfficialMaterialVersion.document_id == document.id)) or 0) + 1
    material = OfficialMaterialVersion(
        document_id=document.id, source_document_version_id=version.id, version_number=next_version,
        kind=document.kind, course_id=document.course_id, subject_id=document.subject_id,
        source_paper_id=document.source_document_id, status="draft", created_by=principal.user.id,
        textbook_content_version_id=_published_textbook_version(db, document).id if document.kind == "past_paper" and not _published_textbook(db, document) else None,
        textbook_id=_published_textbook(db, document).id if document.kind == "past_paper" and _published_textbook(db, document) else None,
    )
    db.add(material); db.flush()
    proposal = _proposal_rows(db, version, document.kind)
    payload = SaveOfficialMaterialReview(expectedItemCount=len(proposal))
    if document.kind == "past_paper": payload.questions = proposal
    elif document.kind == "mark_scheme": payload.markSchemeEntries = proposal
    else: payload.examinerComments = proposal
    _replace(db, material, payload)
    db.add(AuditEvent(actor_id=principal.user.id, action="official_material.proposed", target_type="document", target_id=str(document.id), event_data={"versionNumber": next_version, "kind": document.kind}))
    db.commit(); db.refresh(material)
    return _response(db, material)


def _replace(db: Session, material: OfficialMaterialVersion, payload: SaveOfficialMaterialReview):
    db.execute(delete(OfficialQuestionVersion).where(OfficialQuestionVersion.material_version_id == material.id))
    db.execute(delete(MarkSchemeEntryVersion).where(MarkSchemeEntryVersion.material_version_id == material.id))
    db.execute(delete(ExaminerCommentVersion).where(ExaminerCommentVersion.material_version_id == material.id))
    for q in payload.questions:
        db.add(OfficialQuestionVersion(material_version_id=material.id, question_number=q.number, parent_number=q.parentNumber, prompt=q.prompt, shared_stem=q.sharedStem, marks=q.marks, equations=q.equations, asset_ids=[str(value) for value in q.assetIds], source_locations=[row.model_dump(mode="json") for row in q.sourceLocations]))
    for e in payload.markSchemeEntries:
        db.add(MarkSchemeEntryVersion(material_version_id=material.id, question_number=e.questionNumber, max_marks=e.maxMarks, marking_points=[row.model_dump() for row in e.markingPoints], alternatives=e.alternatives, source_locations=[row.model_dump(mode="json") for row in e.sourceLocations]))
    for c in payload.examinerComments:
        db.add(ExaminerCommentVersion(material_version_id=material.id, question_number=c.questionNumber, common_mistakes=c.commonMistakes, advice=c.advice, source_locations=[row.model_dump(mode="json") for row in c.sourceLocations]))
    material.inventory_count = payload.expectedItemCount
    material.completeness_confirmed = payload.completenessConfirmed


def _validate_sources(db: Session, material: OfficialMaterialVersion, payload: SaveOfficialMaterialReview):
    items = [*payload.questions, *payload.markSchemeEntries, *payload.examinerComments]
    block_ids = {location.blockId for item in items for location in item.sourceLocations}
    valid_block_pages = dict(db.execute(select(DocumentBlock.id, DocumentPage.page_number).join(
        DocumentPage, DocumentPage.id == DocumentBlock.page_id
    ).where(
        DocumentBlock.document_version_id == material.source_document_version_id,
        DocumentBlock.id.in_(block_ids),
    )).all()) if block_ids else {}
    if block_ids != set(valid_block_pages) or any(
        valid_block_pages.get(location.blockId) != location.page
        for item in items for location in item.sourceLocations
    ):
        raise DomainError("invalid_source_location", "Every item must point to a block in this document version.", 422)
    asset_ids = {asset_id for question in payload.questions for asset_id in question.assetIds}
    valid_assets = set(db.scalars(select(DocumentAsset.id).where(
        DocumentAsset.document_version_id == material.source_document_version_id,
        DocumentAsset.id.in_(asset_ids),
    )).all()) if asset_ids else set()
    if asset_ids != valid_assets:
        raise DomainError("invalid_question_asset", "Question assets must come from this document version.", 422)


def save_review(db: Session, principal: Principal, document_id: uuid.UUID, payload: SaveOfficialMaterialReview):
    document = _document(db, document_id)
    material = _current(db, document.id)
    if material and material.status == "published":
        material = None
    if not material:
        version = _source_version(db, document.id)
        next_version = (db.scalar(select(func.max(OfficialMaterialVersion.version_number)).where(OfficialMaterialVersion.document_id == document.id)) or 0) + 1
        logical = _published_textbook(db, document) if document.kind == "past_paper" else None
        material = OfficialMaterialVersion(document_id=document.id, source_document_version_id=version.id, version_number=next_version, kind=document.kind, course_id=document.course_id, subject_id=document.subject_id, source_paper_id=document.source_document_id, created_by=principal.user.id, textbook_content_version_id=_published_textbook_version(db, document).id if document.kind == "past_paper" and not logical else None, textbook_id=logical.id if logical else None)
        db.add(material); db.flush()
    expected_kind_count = len(payload.questions if document.kind == "past_paper" else payload.markSchemeEntries if document.kind == "mark_scheme" else payload.examinerComments)
    if any((payload.questions if document.kind != "past_paper" else [], payload.markSchemeEntries if document.kind != "mark_scheme" else [], payload.examinerComments if document.kind != "examiner_report" else [])):
        raise DomainError("wrong_official_material_content", "Review content must match the document type.", 422)
    if payload.expectedItemCount != expected_kind_count:
        raise DomainError("inventory_mismatch", "Expected item count must match the complete reviewed inventory.", 409)
    _validate_sources(db, material, payload)
    _replace(db, material, payload)
    db.add(AuditEvent(actor_id=principal.user.id, action="official_material.saved", target_type="official_material", target_id=str(material.id), event_data={"versionNumber": material.version_number, "itemCount": expected_kind_count}))
    db.commit(); db.refresh(material)
    return _response(db, material)


def _published_paper_questions(db: Session, paper_id: uuid.UUID) -> tuple[OfficialMaterialVersion, dict[str, int]]:
    paper = db.scalar(select(OfficialMaterialVersion).where(
        OfficialMaterialVersion.document_id == paper_id, OfficialMaterialVersion.kind == "past_paper",
        OfficialMaterialVersion.status == "published",
    ).order_by(OfficialMaterialVersion.version_number.desc()))
    if not paper:
        raise DomainError("published_source_paper_required", "Publish the related past paper before this document.", 409)
    return paper, dict(db.execute(select(OfficialQuestionVersion.question_number, OfficialQuestionVersion.marks).where(OfficialQuestionVersion.material_version_id == paper.id)).all())


def publish_review(db: Session, principal: Principal, document_id: uuid.UUID, confirmation):
    document = _document(db, document_id)
    material = _current(db, document.id)
    if not material or material.status != "draft":
        raise DomainError("official_material_draft_required", "Save an official-material review draft first.", 409)
    if not confirmation.confirmCourse or not confirmation.confirmSubject or not confirmation.confirmComplete:
        raise DomainError("official_material_confirmation_required", "Confirm course, subject and completeness before publishing.", 422)
    count = db.scalar(select(func.count()).select_from(OfficialQuestionVersion if material.kind == "past_paper" else MarkSchemeEntryVersion if material.kind == "mark_scheme" else ExaminerCommentVersion).where((OfficialQuestionVersion if material.kind == "past_paper" else MarkSchemeEntryVersion if material.kind == "mark_scheme" else ExaminerCommentVersion).material_version_id == material.id))
    if not material.completeness_confirmed or count == 0 or count != material.inventory_count:
        raise DomainError("official_material_incomplete", "Complete and attest the full source inventory before publishing.", 409)
    if material.kind != "past_paper":
        if not confirmation.confirmSourcePaper or not material.source_paper_id:
            raise DomainError("source_paper_confirmation_required", "Confirm the related published past paper.", 422)
        source_paper_version, allowed = _published_paper_questions(db, material.source_paper_id)
        material.source_paper_version_id = source_paper_version.id
        material.textbook_content_version_id = source_paper_version.textbook_content_version_id
        material.textbook_id = source_paper_version.textbook_id
        model = MarkSchemeEntryVersion if material.kind == "mark_scheme" else ExaminerCommentVersion
        numbers = set(db.scalars(select(model.question_number).where(model.material_version_id == material.id)).all())
        if not numbers.issubset(allowed):
            raise DomainError("unmatched_question_reference", "Every entry must reference a question in the published source paper.", 409)
        if material.kind == "mark_scheme":
            entries = db.scalars(select(MarkSchemeEntryVersion).where(MarkSchemeEntryVersion.material_version_id == material.id)).all()
            if numbers != set(allowed) or any(entry.max_marks != allowed[entry.question_number] for entry in entries):
                raise DomainError("mark_scheme_reconciliation_failed", "The marking scheme must cover every published question with matching marks.", 409)
    now = datetime.now(timezone.utc)
    for old in db.scalars(select(OfficialMaterialVersion).where(OfficialMaterialVersion.document_id == document.id, OfficialMaterialVersion.status == "published").with_for_update()).all():
        old.status = "superseded"; old.superseded_at = now
    material.status = "published"; material.published_by = principal.user.id; material.published_at = now
    document.review_state = "published"
    db.add(AuditEvent(actor_id=principal.user.id, action="official_material.published", target_type="official_material", target_id=str(material.id), event_data={"versionNumber": material.version_number, "itemCount": count}))
    db.commit(); db.refresh(material)
    return _response(db, material)
