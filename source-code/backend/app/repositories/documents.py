import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Course, Document, DocumentAsset, DocumentBlock, DocumentEvent, DocumentJob, DocumentPage,
    DocumentStageRun, DocumentVersion, Subject, Textbook,
)


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def document(self, document_id: uuid.UUID) -> Document | None:
        return self.db.get(Document, document_id)

    def version(self, version_id: uuid.UUID) -> DocumentVersion | None:
        return self.db.get(DocumentVersion, version_id)

    def latest_version(self, document_id: uuid.UUID) -> DocumentVersion | None:
        return self.db.execute(select(DocumentVersion).where(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.version_number.desc())).scalars().first()

    def job(self, job_id: uuid.UUID, *, lock: bool = False) -> DocumentJob | None:
        query = select(DocumentJob).where(DocumentJob.id == job_id)
        if lock:
            query = query.with_for_update(skip_locked=True)
        return self.db.execute(query).scalar_one_or_none()

    def latest_job(self, document_id: uuid.UUID) -> DocumentJob | None:
        return self.db.execute(select(DocumentJob).where(
            DocumentJob.document_id == document_id
        ).order_by(DocumentJob.queued_at.desc())).scalars().first()

    def queued_job_ids(self) -> list[uuid.UUID]:
        return list(self.db.execute(select(DocumentJob.id).where(
            DocumentJob.status == "queued"
        ).order_by(DocumentJob.queued_at)).scalars())

    def stage_run(
        self, version_id: uuid.UUID, stage: str, extraction_version: str
    ) -> DocumentStageRun | None:
        return self.db.execute(select(DocumentStageRun).where(
            DocumentStageRun.document_version_id == version_id,
            DocumentStageRun.stage == stage,
            DocumentStageRun.extraction_version == extraction_version,
        )).scalar_one_or_none()

    def pages_with_blocks(self, version_id: uuid.UUID) -> list[tuple[DocumentPage, list[DocumentBlock]]]:
        pages = list(self.db.execute(select(DocumentPage).where(
            DocumentPage.document_version_id == version_id
        ).order_by(DocumentPage.page_number)).scalars())
        if not pages:
            return []
        blocks = list(self.db.execute(select(DocumentBlock).where(
            DocumentBlock.page_id.in_([page.id for page in pages])
        ).order_by(DocumentBlock.page_id, DocumentBlock.sequence_number)).scalars())
        by_page: dict[uuid.UUID, list[DocumentBlock]] = {page.id: [] for page in pages}
        for block in blocks:
            by_page[block.page_id].append(block)
        return [(page, by_page[page.id]) for page in pages]

    def asset(self, asset_id: uuid.UUID) -> DocumentAsset | None:
        return self.db.get(DocumentAsset, asset_id)

    def checksum_exists(self, checksum: str) -> bool:
        return self.db.execute(select(DocumentVersion.id).where(
            DocumentVersion.sha256 == checksum
        )).scalar_one_or_none() is not None

    def active_documents(self) -> list[tuple[Document, DocumentVersion]]:
        # Every Step 2 document has one version. The version-number join keeps this
        # correct when immutable replacement versions are added later.
        latest = (
            select(
                DocumentVersion.document_id,
                func.max(DocumentVersion.version_number).label("version_number"),
            )
            .group_by(DocumentVersion.document_id)
            .subquery()
        )
        query = (
            select(Document, DocumentVersion)
            .join(latest, latest.c.document_id == Document.id)
            .join(
                DocumentVersion,
                (DocumentVersion.document_id == latest.c.document_id)
                & (DocumentVersion.version_number == latest.c.version_number),
            )
            .where(Document.removed_at.is_(None))
            .order_by(Document.created_at.desc())
        )
        return list(self.db.execute(query).all())

    def course_and_subject_exist(self, course_id: str, subject_id: str) -> bool:
        course = self.db.get(Course, course_id)
        subject = self.db.get(Subject, subject_id)
        return bool(course and course.phase1_active and subject)

    def has_textbook(self, course_id: str, subject_id: str) -> bool:
        return self.db.execute(
            select(Textbook.id).where(
                Textbook.course_id == course_id, Textbook.subject_id == subject_id,
                Textbook.status == "published",
            )
        ).scalars().first() is not None

    def source_paper(self, source_id: uuid.UUID) -> Document | None:
        return self.db.execute(select(Document).where(
            Document.id == source_id,
            Document.kind == "past_paper",
            Document.removed_at.is_(None),
        )).scalar_one_or_none()

    def add_event(
        self,
        document: Document,
        version: DocumentVersion | None,
        actor_id: uuid.UUID,
        event_type: str,
        event_data: dict | None = None,
    ) -> None:
        self.db.add(DocumentEvent(
            document_id=document.id,
            document_version_id=version.id if version else None,
            actor_id=actor_id,
            event_type=event_type,
            event_data=event_data or {},
        ))
