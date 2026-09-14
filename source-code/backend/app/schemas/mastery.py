import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class MasteryDimensionResponse(BaseModel):
    dimension: str
    score: float = Field(ge=0, le=10)
    evidenceWeight: float = Field(ge=0)

class MasteryEventResponse(BaseModel):
    id: uuid.UUID
    previousScore: float | None
    newScore: float
    previousConfidence: str | None
    newConfidence: str
    explanation: str
    createdAt: datetime

class UnitMasteryResponse(BaseModel):
    unitId: uuid.UUID
    unitCode: str
    unitTitle: str
    subjectId: str
    score: float = Field(ge=0, le=10)
    preciseScore: float = Field(ge=0, le=10)
    confidence: str
    provisional: bool
    evidenceCount: int
    evidenceWeight: float
    varietyCount: int
    trend: float
    lastEvidenceAt: datetime
    dimensions: list[MasteryDimensionResponse]
    recentEvents: list[MasteryEventResponse]

class MasteryResponse(BaseModel):
    studentId: uuid.UUID
    units: list[UnitMasteryResponse]

class HintInteractionRequest(BaseModel):
    idempotencyKey: str = Field(min_length=8, max_length=100)

class HintInteractionResponse(BaseModel):
    hint: str
    total: int
