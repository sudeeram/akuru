import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, exists, or_, select, update
from sqlalchemy.orm import Session

from app.config import Settings
from app.errors import DomainError
from app.models import (
    Document, DocumentBlock, DocumentPage, ExaminerCommentVersion, MarkSchemeEntryVersion,
    OfficialMaterialVersion, OfficialQuestionUnitMapping, OfficialQuestionVersion,
    RetrievalChunk, StudentProfile, StudentSubject, TextbookContentVersion, TextbookUnit, TextbookUnitVersion,
)
from app.schemas.retrieval import EvidenceResponse, ReindexResponse, RetrievalResponse
from app.security import Principal
from app.services.curriculum_plans import student_coverage
from app.services.embeddings import embed_texts


def authorize_student(db: Session, principal: Principal, student_id: uuid.UUID, subject_id: str) -> set[uuid.UUID]:
    profile = db.get(StudentProfile, student_id)
    if not profile:
        raise DomainError("student_not_found", "Student not found.", 404)
    if principal.user.role == "student" and principal.user.id != student_id:
        raise DomainError("student_access_denied", "Students may only use their own learning sources.", 403)
    if principal.user.role == "parent" and profile.parent_id != principal.user.id:
        raise DomainError("student_access_denied", "This student is not linked to your parent account.", 403)
    if not db.get(StudentSubject, (student_id, subject_id)):
        raise DomainError("subject_not_assigned", "This subject is not assigned to the student.", 403)
    coverage = student_coverage(db, student_id, subject_id)
    if coverage.status != "ready":
        raise DomainError("retrieval_coverage_not_ready", coverage.message, 409)
    return {uuid.UUID(unit.id) for unit in coverage.coveredUnits}


def _location(locations: list, ordinal: int) -> tuple[int, dict, uuid.UUID | None]:
    raw = locations[min(ordinal, len(locations) - 1)] if locations else {}
    asset = raw.get("assetId") or raw.get("sourceAssetId")
    return int(raw.get("page", 1)), raw.get("boundingBox") or {}, uuid.UUID(asset) if asset else None


def _add(rows: list[dict], **kwargs) -> None:
    content = " ".join(str(kwargs.pop("content")).split())
    if content:
        kwargs["content"] = content
        kwargs["content_hash"] = hashlib.sha256(content.encode()).hexdigest()
        rows.append(kwargs)


def _textbook_rows(db: Session, document: Document, version: TextbookContentVersion) -> list[dict]:
    units = db.scalars(select(TextbookUnit).where(
        TextbookUnit.content_version_id == version.id
    )).all()
    rows: list[dict] = []
    for unit in units:
        unit_version = db.scalar(select(TextbookUnitVersion).where(
            TextbookUnitVersion.content_version_id == version.id,
            TextbookUnitVersion.unit_code == unit.unit_code,
        ))
        if not unit_version:
            continue
        blocks = db.execute(select(DocumentBlock, DocumentPage.page_number).join(
            DocumentPage, DocumentPage.id == DocumentBlock.page_id
        ).where(
            DocumentBlock.document_version_id == version.source_document_version_id,
            DocumentPage.page_number.between(unit_version.start_page, unit_version.end_page),
            DocumentBlock.needs_review.is_(False),
        ).order_by(DocumentPage.page_number, DocumentBlock.sequence_number)).all()
        for ordinal, (block, page) in enumerate(blocks):
            _add(rows, document_id=document.id, document_version_id=version.source_document_version_id,
                 textbook_content_version_id=version.id, official_material_version_id=None,
                 unit_id=unit.id, course_id=version.course_id, subject_id=version.subject_id,
                 source_type="textbook_section", source_item_id=block.id, source_ordinal=ordinal,
                 content=block.latex or block.text, page_number=page, bounding_box=block.bounding_box,
                 source_asset_id=block.source_asset_id)
    return rows


def _mapped_units(db: Session, material: OfficialMaterialVersion, question_number: str) -> list[uuid.UUID]:
    paper_version_id = material.source_paper_version_id
    if not paper_version_id:
        return []
    question = db.scalar(select(OfficialQuestionVersion).where(
        OfficialQuestionVersion.material_version_id == paper_version_id,
        OfficialQuestionVersion.question_number == question_number,
        OfficialQuestionVersion.mapping_status == "confirmed",
    ))
    if not question:
        return []
    return list(db.scalars(select(OfficialQuestionUnitMapping.unit_id).where(
        OfficialQuestionUnitMapping.question_version_id == question.id,
        OfficialQuestionUnitMapping.status == "confirmed",
    )).all())


def _official_rows(db: Session, document: Document, material: OfficialMaterialVersion) -> list[dict]:
    rows: list[dict] = []
    if material.kind == "mark_scheme":
        items = db.scalars(select(MarkSchemeEntryVersion).where(MarkSchemeEntryVersion.material_version_id == material.id)).all()
        values = lambda item: item.marking_points
        source_type = "marking_point"
    elif material.kind == "examiner_report":
        items = db.scalars(select(ExaminerCommentVersion).where(ExaminerCommentVersion.material_version_id == material.id)).all()
        values = lambda item: list(item.common_mistakes) + list(item.advice)
        source_type = "examiner_guidance"
    else:
        return rows
    for item in items:
        units = _mapped_units(db, material, item.question_number)
        for value_index, value in enumerate(values(item)):
            content = value.get("text", "") if isinstance(value, dict) else str(value)
            page, bbox, asset = _location(item.source_locations, value_index)
            for unit_index, unit_id in enumerate(units):
                _add(rows, document_id=document.id, document_version_id=material.source_document_version_id,
                     textbook_content_version_id=material.textbook_content_version_id,
                     official_material_version_id=material.id, unit_id=unit_id,
                     course_id=material.course_id, subject_id=material.subject_id,
                     source_type=source_type, source_item_id=item.id,
                     source_ordinal=value_index * 100 + unit_index, content=content,
                     page_number=page, bounding_box=bbox, source_asset_id=asset)
    return rows


def reindex_document(db: Session, settings: Settings, document_id: uuid.UUID) -> ReindexResponse:
    document = db.get(Document, document_id)
    if not document or document.removed_at or document.review_state != "published":
        raise DomainError("published_document_required", "Only a published document can be indexed.", 409)
    if document.kind == "textbook":
        version = db.scalar(select(TextbookContentVersion).where(
            TextbookContentVersion.document_id == document.id, TextbookContentVersion.status == "published"
        ).order_by(TextbookContentVersion.version_number.desc()))
        rows = _textbook_rows(db, document, version) if version else []
    else:
        version = db.scalar(select(OfficialMaterialVersion).where(
            OfficialMaterialVersion.document_id == document.id, OfficialMaterialVersion.status == "published"
        ).order_by(OfficialMaterialVersion.version_number.desc()))
        rows = _official_rows(db, document, version) if version else []
    now = datetime.now(timezone.utc)
    superseded = db.execute(update(RetrievalChunk).where(
        RetrievalChunk.document_id == document.id, RetrievalChunk.status == "active"
    ).values(status="superseded", superseded_at=now)).rowcount
    embeddings = embed_texts(settings, [row["content"] for row in rows]) if rows else []
    next_versions: dict[tuple, int] = {}
    for row, embedding in zip(rows, embeddings):
        key = (row["source_type"], row["source_item_id"], row["source_ordinal"])
        if key not in next_versions:
            prior = db.scalar(select(RetrievalChunk.embedding_version).where(
                RetrievalChunk.source_type == key[0], RetrievalChunk.source_item_id == key[1],
                RetrievalChunk.source_ordinal == key[2],
            ).order_by(RetrievalChunk.embedding_version.desc()))
            next_versions[key] = (prior or 0) + 1
        db.add(RetrievalChunk(**row, embedding=embedding, embedding_model=settings.embedding_model,
                              embedding_version=next_versions[key]))
    db.commit()
    return ReindexResponse(documentId=document.id, indexedChunks=len(rows), supersededChunks=superseded,
                           embeddingModel=settings.embedding_model)


def retrieve(db: Session, settings: Settings, principal: Principal, student_id: uuid.UUID,
             subject_id: str, query: str, limit: int) -> RetrievalResponse:
    units = authorize_student(db, principal, student_id, subject_id)
    vector = embed_texts(settings, [query])[0]
    distance = RetrievalChunk.embedding.cosine_distance(vector)
    records = db.execute(select(RetrievalChunk, Document, TextbookUnit, distance.label("distance")).join(
        Document, Document.id == RetrievalChunk.document_id
    ).join(TextbookUnit, TextbookUnit.id == RetrievalChunk.unit_id).where(
        RetrievalChunk.status == "active", RetrievalChunk.course_id == "igcse",
        RetrievalChunk.subject_id == subject_id, RetrievalChunk.unit_id.in_(units),
        Document.review_state == "published", Document.removed_at.is_(None),
        or_(
            and_(RetrievalChunk.source_type == "textbook_section", exists(select(TextbookContentVersion.id).where(
                TextbookContentVersion.id == RetrievalChunk.textbook_content_version_id,
                TextbookContentVersion.status == "published",
            ))),
            and_(RetrievalChunk.source_type.in_(("marking_point", "examiner_guidance")), exists(select(OfficialMaterialVersion.id).where(
                OfficialMaterialVersion.id == RetrievalChunk.official_material_version_id,
                OfficialMaterialVersion.status == "published",
            ))),
        ),
    ).order_by(distance).limit(limit)).all()
    evidence = [EvidenceResponse(
        chunkId=chunk.id, sourceType=chunk.source_type, content=chunk.content,
        documentId=document.id, documentTitle=document.title, page=chunk.page_number,
        boundingBox=chunk.bounding_box, sourceAssetId=chunk.source_asset_id,
        sourceUrl=f"/api/v1/retrieval/evidence/{chunk.id}?studentId={student_id}",
        unitId=unit.id, unitCode=unit.unit_code, unitTitle=unit.title,
        score=max(0.0, 1.0 - float(distance_value)),
    ) for chunk, document, unit, distance_value in records]
    return RetrievalResponse(query=query, subjectId=subject_id, evidence=evidence)


def evidence(db: Session, principal: Principal, settings: Settings, chunk_id: uuid.UUID,
             student_id: uuid.UUID) -> EvidenceResponse:
    chunk = db.get(RetrievalChunk, chunk_id)
    if not chunk or chunk.status != "active":
        raise DomainError("evidence_not_found", "Evidence not found.", 404)
    units = authorize_student(db, principal, student_id, chunk.subject_id)
    if chunk.unit_id not in units:
        raise DomainError("evidence_not_found", "Evidence not found.", 404)
    document = db.get(Document, chunk.document_id)
    unit = db.get(TextbookUnit, chunk.unit_id)
    source_published = (db.get(TextbookContentVersion, chunk.textbook_content_version_id).status == "published"
        if chunk.source_type == "textbook_section" and chunk.textbook_content_version_id
        else bool(chunk.official_material_version_id and db.get(OfficialMaterialVersion, chunk.official_material_version_id)
                  and db.get(OfficialMaterialVersion, chunk.official_material_version_id).status == "published"))
    if not document or document.review_state != "published" or document.removed_at or not source_published:
        raise DomainError("evidence_not_found", "Evidence not found.", 404)
    return EvidenceResponse(chunkId=chunk.id, sourceType=chunk.source_type, content=chunk.content,
        documentId=document.id, documentTitle=document.title, page=chunk.page_number,
        boundingBox=chunk.bounding_box, sourceAssetId=chunk.source_asset_id,
        sourceUrl=f"/api/v1/retrieval/evidence/{chunk.id}?studentId={student_id}",
        unitId=unit.id, unitCode=unit.unit_code, unitTitle=unit.title)
