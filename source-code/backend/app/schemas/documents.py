from enum import StrEnum
from datetime import datetime

from pydantic import BaseModel, Field


class DocumentType(StrEnum):
    TEXTBOOK = "textbook"
    REFERENCE = "reference"
    PAST_PAPER = "past_paper"
    MARK_SCHEME = "mark_scheme"
    EXAMINER_REPORT = "examiner_report"


class DocumentResponse(BaseModel):
    id: str
    kind: DocumentType
    courseId: str
    subjectId: str
    title: str
    originalFilename: str
    contentType: str
    sizeBytes: int
    checksum: str
    status: str
    edition: str | None = None
    year: int | None = None
    session: str | None = None
    component: str | None = None
    variant: str | None = None
    sourceDocumentId: str | None = None
    sourceMetadata: dict = Field(default_factory=dict)
    versionId: str
    versionNumber: int
    createdAt: datetime
    removedAt: datetime | None = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]


class DocumentActionResponse(BaseModel):
    id: str
    status: str
