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


class DocumentJobResponse(BaseModel):
    id: str
    documentId: str
    documentVersionId: str
    stage: str
    status: str
    progress: int
    attemptCount: int
    extractionVersion: str
    errorCode: str | None = None
    errorMessage: str | None = None
    result: dict = Field(default_factory=dict)
    queuedAt: datetime
    startedAt: datetime | None = None
    completedAt: datetime | None = None


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    job: DocumentJobResponse


class ExtractionBlockResponse(BaseModel):
    id: str
    sequenceNumber: int
    kind: str
    text: str
    latex: str | None = None
    boundingBox: dict
    method: str
    confidence: float
    needsReview: bool
    sourceAssetId: str | None = None
    metadata: dict = Field(default_factory=dict)


class ExtractionPageResponse(BaseModel):
    id: str
    pageNumber: int
    widthPoints: float
    heightPoints: float
    renderAssetId: str
    method: str
    confidence: float
    needsReview: bool
    metadata: dict = Field(default_factory=dict)
    blocks: list[ExtractionBlockResponse] = Field(default_factory=list)


class DocumentExtractionResponse(BaseModel):
    documentId: str
    versionId: str
    status: str
    pages: list[ExtractionPageResponse] = Field(default_factory=list)
