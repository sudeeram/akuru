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
    topicRef: str
    topicCode: str
    topicTitle: str
    groupLabel: str
    groupCode: str
    groupTitle: str
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
