import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.assessments import AssessmentQuestionResponse


class TutorPracticeStart(BaseModel):
    requestKey: str = Field(min_length=8, max_length=100)


class TutorPracticeAnswer(BaseModel):
    answer: str = Field(default="", max_length=100_000)
    requestKey: str = Field(min_length=8, max_length=100)


class TutorPracticeAction(BaseModel):
    requestKey: str = Field(min_length=8, max_length=100)


class TutorPracticeResponse(BaseModel):
    practiceRef: str
    status: Literal["active", "submitted"]
    unitCode: str
    unitTitle: str
    question: AssessmentQuestionResponse
    assetUrls: list[str] = Field(default_factory=list)
    hintCount: int
    latestHint: str | None = None
    feedbackVisible: bool
    createdAt: datetime
    submittedAt: datetime | None = None


class TutorSignalResponse(BaseModel):
    signalRef: str
    studentName: str
    subjectId: str
    unitCode: str
    unitTitle: str
    category: str
    observation: str
    confidence: float
    evidenceCount: int
    promptName: str
    promptVersion: str
    createdAt: datetime


class TutorSignalListResponse(BaseModel):
    signals: list[TutorSignalResponse]
