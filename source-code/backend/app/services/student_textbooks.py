"""Student reader over published structure and Topic evidence snapshots."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import DomainError
from app.models import (DocumentAsset, DocumentBlock, DocumentPage, RetrievalChunk,
                        StudentSubject, Textbook, TextbookStructureVersion,
                        TextbookTopic, TextbookTopicContentVersion)
from app.schemas.student_textbooks import (StudentTextbook, StudentTextbookGroup,
    StudentTextbookList, StudentTextbookPage, StudentTextbookSection,
    StudentTextbookTopic, StudentTextbookTopicContent, StudentTextbookVisual)
from app.security import Principal
from app.storage import ObjectStorage


def _released(db: Session, principal: Principal, book_ref: str, topic_ref: str | None = None):
    book = db.scalar(select(Textbook).where(Textbook.public_ref == book_ref,
                                            Textbook.archived_at.is_(None)))
    if not book or not db.get(StudentSubject, (principal.user.id, book.subject_id)):
        raise DomainError("textbook_not_available", "This textbook is not available in your subjects.", 404)
    structure = db.scalar(select(TextbookStructureVersion).where(
        TextbookStructureVersion.textbook_id == book.id).order_by(
        TextbookStructureVersion.version_number.desc()))
    if not structure:
        raise DomainError("textbook_not_available", "This textbook is not published yet.", 404)
    if topic_ref is None:
        return book, structure, None, None
    snapshot_topic = next(((group, topic) for group in structure.snapshot.get("groups", [])
                           for topic in group.get("topics", []) if topic.get("topicRef") == topic_ref), None)
    topic = db.scalar(select(TextbookTopic).where(TextbookTopic.public_ref == topic_ref,
                                                  TextbookTopic.textbook_id == book.id))
    content = db.scalar(select(TextbookTopicContentVersion).where(
        TextbookTopicContentVersion.topic_id == topic.id,
        TextbookTopicContentVersion.status == "published")) if topic else None
    if not snapshot_topic or not content:
        raise DomainError("topic_not_available", "This textbook Topic is not published yet.", 404)
    return book, structure, (topic, snapshot_topic[0], snapshot_topic[1]), content


def list_books(db: Session, principal: Principal) -> StudentTextbookList:
    subject_ids = db.scalars(select(StudentSubject.subject_id).where(
        StudentSubject.student_id == principal.user.id)).all()
    if not subject_ids:
        return StudentTextbookList(textbooks=[])
    books = db.scalars(select(Textbook).where(Textbook.subject_id.in_(subject_ids),
                                              Textbook.archived_at.is_(None)).order_by(
        Textbook.subject_id, Textbook.title, Textbook.edition)).all()
    result = []
    for book in books:
        structure = db.scalar(select(TextbookStructureVersion).where(
            TextbookStructureVersion.textbook_id == book.id).order_by(
            TextbookStructureVersion.version_number.desc()))
        if not structure:
            continue
        topic_refs = [topic.get("topicRef") for group in structure.snapshot.get("groups", [])
                      for topic in group.get("topics", [])]
        released = db.execute(select(TextbookTopic.public_ref,
            TextbookTopicContentVersion).join(
            TextbookTopicContentVersion,
            TextbookTopicContentVersion.topic_id == TextbookTopic.id).where(
            TextbookTopic.textbook_id == book.id,
            TextbookTopic.public_ref.in_(topic_refs),
            TextbookTopicContentVersion.status == "published")).all()
        released_topics = {ref: content for ref, content in released}
        page_counts = {ref: sum(len(source.get("pages", [])) for source in content.source_manifest
                                if source.get("role") == "primary") for ref, content in released_topics.items()}
        groups = [StudentTextbookGroup(code=group["code"], title=group["title"],
            topics=[StudentTextbookTopic(topicRef=topic["topicRef"], code=topic["code"],
                title=topic["title"], pageCount=page_counts[topic["topicRef"]],
                contentVersion=released_topics[topic["topicRef"]].version_number,
                publishedAt=released_topics[topic["topicRef"]].published_at.isoformat())
                for topic in group.get("topics", []) if page_counts.get(topic.get("topicRef"), 0) > 0])
            for group in structure.snapshot.get("groups", [])]
        groups = [group for group in groups if group.topics]
        if groups:
            result.append(StudentTextbook(textbookRef=book.public_ref, subjectId=book.subject_id,
                title=book.title, edition=book.edition, publisher=book.publisher,
                groupLabel=book.group_label, structureVersion=structure.version_number,
                structurePublishedAt=structure.published_at.isoformat(), groups=groups))
    return StudentTextbookList(textbooks=result)


def topic_content(db: Session, principal: Principal, book_ref: str,
                  topic_ref: str) -> StudentTextbookTopicContent:
    book, _structure, (topic, group_snapshot, topic_snapshot), content = _released(
        db, principal, book_ref, topic_ref)
    source_ids = {source.get("documentVersionId") for source in content.source_manifest
                  if source.get("role") == "primary"}
    chunks = db.scalars(select(RetrievalChunk).where(
        RetrievalChunk.topic_content_version_id == content.id,
        RetrievalChunk.topic_id == topic.id,
        RetrievalChunk.source_type == "textbook_section",
        RetrievalChunk.status == "active").order_by(RetrievalChunk.source_ordinal)).all()
    block_ids = {chunk.source_item_id for chunk in chunks}
    kinds = {block.id: block.block_kind for block in db.scalars(select(DocumentBlock).where(
        DocumentBlock.id.in_(block_ids))).all()} if block_ids else {}
    visual_rows = content.extraction_manifest.get("visualAssets", [])
    def visual_payload(row):
        return StudentTextbookVisual(assetRef=row["assetRef"], caption=row.get("caption", ""),
            altText=row.get("altText", ""),
            contentUrl=f"/api/v1/student/textbooks/{book_ref}/topics/{topic_ref}/visuals/{row['assetRef']}")
    pages = []
    attached_visual_refs = set()
    for source in sorted(content.source_manifest, key=lambda item: item.get("sequence", 0)):
        if source.get("role") != "primary":
            continue
        version_id = source.get("documentVersionId")
        for page in source.get("pages", []):
            number = page["pageNumber"]
            sections = [StudentTextbookSection(kind=kinds.get(chunk.source_item_id, "paragraph"),
                                                text=chunk.content)
                        for chunk in chunks if str(chunk.document_version_id) == version_id
                        and chunk.page_number == number]
            matching = [row for row in visual_rows if row.get("documentVersionId") == version_id
                and row.get("pageNumber") == number]
            visuals = [visual_payload(row) for row in matching]
            attached_visual_refs.update(row["assetRef"] for row in matching)
            ordinal = len(pages) + 1
            pages.append(StudentTextbookPage(ordinal=ordinal, pageNumber=number,
                printedPage=page.get("printedPageLabel"),
                imageUrl=f"/api/v1/student/textbooks/{book_ref}/topics/{topic_ref}/pages/{ordinal}/image",
                sections=sections, visuals=visuals))
    # Approved visuals from the Visual Reference are attached by the reviewed
    # printed page label; the snapshot alone decides what a Student may see.
    for row in visual_rows:
        if row["assetRef"] in attached_visual_refs or row.get("documentVersionId") in source_ids:
            continue
        matching = next((page for page in pages if page.printedPage and
                         page.printedPage == row.get("printedPageLabel")), None)
        if matching:
            matching.visuals.append(visual_payload(row))
            attached_visual_refs.add(row["assetRef"])
    return StudentTextbookTopicContent(textbookRef=book.public_ref, textbookTitle=book.title,
        subjectId=book.subject_id, groupCode=group_snapshot["code"],
        groupTitle=group_snapshot["title"], topicRef=topic.public_ref,
        topicCode=topic_snapshot["code"], topicTitle=topic_snapshot["title"],
        contentVersion=content.version_number, publishedAt=content.published_at.isoformat(),
        pages=pages, additionalVisuals=[visual_payload(row) for row in visual_rows
            if row["assetRef"] not in attached_visual_refs])


def page_image(db: Session, storage: ObjectStorage, principal: Principal,
               book_ref: str, topic_ref: str, ordinal: int):
    _book, _structure, _topic, content = _released(db, principal, book_ref, topic_ref)
    published_pages = [(source["documentVersionId"], page["pageNumber"])
        for source in sorted(content.source_manifest, key=lambda item: item.get("sequence", 0))
        if source.get("role") == "primary" for page in source.get("pages", [])]
    if 1 <= ordinal <= len(published_pages):
        version_id, page_number = published_pages[ordinal - 1]
        page = db.scalar(select(DocumentPage).where(
            DocumentPage.document_version_id == uuid.UUID(version_id),
            DocumentPage.page_number == page_number))
        asset = db.get(DocumentAsset, page.render_asset_id) if page else None
        if asset and str(asset.document_version_id) == version_id:
            return storage.get(asset.object_key, asset.mime_type)
    raise DomainError("textbook_page_not_available", "This published page is unavailable.", 404)


def visual_image(db: Session, storage: ObjectStorage, principal: Principal,
                 book_ref: str, topic_ref: str, asset_ref: str):
    _book, _structure, _topic, content = _released(db, principal, book_ref, topic_ref)
    visual = next((row for row in content.extraction_manifest.get("visualAssets", [])
                   if row.get("assetRef") == asset_ref), None)
    if not visual:
        raise DomainError("textbook_visual_not_available", "This visual is not published.", 404)
    asset = db.get(DocumentAsset, uuid.UUID(visual["documentAssetId"]))
    if not asset or str(asset.document_version_id) != visual.get("documentVersionId"):
        raise DomainError("textbook_visual_not_available", "This visual is unavailable.", 404)
    return storage.get(asset.object_key, asset.mime_type)
