import uuid
from pydantic import BaseModel, Field


class RetrievalRequest(BaseModel):
    studentId: uuid.UUID
    subjectId: str
    query: str = Field(min_length=2, max_length=2000)
    limit: int = Field(default=6, ge=1, le=20)


class ReindexRequest(BaseModel):
    documentId: uuid.UUID


class EvidenceResponse(BaseModel):
    chunkId: uuid.UUID
    sourceType: str
    content: str
    documentId: uuid.UUID
    documentTitle: str
    page: int
    boundingBox: dict
    sourceAssetId: uuid.UUID | None
    sourceUrl: str
    unitId: uuid.UUID
    unitCode: str
    unitTitle: str
    score: float | None = None


class RetrievalResponse(BaseModel):
    query: str
    subjectId: str
    evidence: list[EvidenceResponse]


class ReindexResponse(BaseModel):
    documentId: uuid.UUID
    indexedChunks: int
    supersededChunks: int
    embeddingModel: str
