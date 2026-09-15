from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class TutorSummaryResponse(BaseModel):
    summaryRef: str; sessionRef: str; studentName: str; subjectId: str
    unitsCovered: list[dict]; activities: list[str]; strengths: list[str]
    difficulties: list[str]; suggestedNextSteps: list[str]; usage: dict; createdAt: datetime


class TutorSummaryListResponse(BaseModel):
    summaries: list[TutorSummaryResponse]


class SafetyEventResponse(BaseModel):
    eventRef: str; studentName: str; category: str
    severity: Literal["low", "medium", "high", "critical"]
    action: str; notificationStatus: str; reviewStatus: str; createdAt: datetime


class SafetyEventListResponse(BaseModel):
    events: list[SafetyEventResponse]


class SafetyReviewRequest(BaseModel):
    status: Literal["reviewed", "resolved"]
    note: str = Field(min_length=3, max_length=500)


class SupportAccessRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


class SupportTranscriptResponse(BaseModel):
    sessionRef: str; studentName: str; turns: list[dict]


class PurgeRequest(BaseModel):
    olderThanDays: int = Field(ge=1, le=3650)
    reason: str = Field(min_length=5, max_length=500)
    confirmation: Literal["PURGE TRANSCRIPTS"]


class PurgePreviewResponse(BaseModel):
    olderThanDays: int; cutoff: datetime; turnCount: int; sessionCount: int


class PurgeResultResponse(PurgePreviewResponse):
    purgedTurnCount: int
