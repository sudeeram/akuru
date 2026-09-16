import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class RecommendationReview(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    reason: str = Field(default="", max_length=500)

class RecommendationResponse(BaseModel):
    id: uuid.UUID
    diagnosisId: uuid.UUID
    studentId: uuid.UUID
    subjectId: str
    unitId: uuid.UUID | None = None
    unitCode: str | None = None
    unitTitle: str | None = None
    topicRef: str | None = None
    topicCode: str | None = None
    topicTitle: str | None = None
    groupLabel: str | None = None
    groupCode: str | None = None
    groupTitle: str | None = None
    category: str
    description: str
    observedEvidence: list[str]
    occurrenceCount: int
    activityType: str
    title: str
    reason: str
    action: str
    successCondition: str
    sourceTitle: str
    sourcePage: int
    sourceUrl: str
    questionId: uuid.UUID | None
    reviewStatus: str
    reviewReason: str
    createdAt: datetime

class RecommendationListResponse(BaseModel):
    recommendations: list[RecommendationResponse]
