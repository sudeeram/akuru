from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.curriculum_plans import PlanTopicResponse
from app.schemas.tutor_profiles import TutorProfileResponse


class TutorSessionStartRequest(BaseModel):
    subjectId: str = Field(min_length=2, max_length=32)
    topicRef: str = Field(min_length=8, max_length=80)
    profileRef: str = Field(min_length=8, max_length=48)
    requestKey: str = Field(min_length=8, max_length=100)


class TutorTurnCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    modality: Literal["text", "voice"] = "text"
    requestKey: str = Field(min_length=8, max_length=100)


class TutorSwitchProfileRequest(BaseModel):
    profileRef: str = Field(min_length=8, max_length=48)
    requestKey: str = Field(min_length=8, max_length=100)


class TutorSwitchTopicRequest(BaseModel):
    topicRef: str = Field(min_length=8, max_length=80)
    requestKey: str = Field(min_length=8, max_length=100)


class TutorEndSessionRequest(BaseModel):
    requestKey: str = Field(min_length=8, max_length=100)


class TutorTurnResponse(BaseModel):
    turnRef: str
    role: Literal["student", "assistant"]
    modality: Literal["text", "voice"]
    content: str
    sequence: int
    profileRef: str
    profileVersion: int
    sources: list[str] = Field(default_factory=list)
    structured: dict = Field(default_factory=dict)
    createdAt: datetime


class TutorProfileEventResponse(BaseModel):
    fromProfileRef: str
    fromProfileVersion: int
    toProfileRef: str
    toProfileVersion: int
    handoverSummary: dict
    createdAt: datetime


class TutorTopicEventResponse(BaseModel):
    fromTopic: PlanTopicResponse
    toTopic: PlanTopicResponse
    createdAt: datetime


class TutorSessionResponse(BaseModel):
    sessionRef: str
    subjectId: str
    activeTopic: PlanTopicResponse
    currentTutor: TutorProfileResponse
    mode: Literal["practice"]
    status: Literal["active", "ended"]
    startedAt: datetime
    endedAt: datetime | None = None
    turns: list[TutorTurnResponse] = Field(default_factory=list)
    profileEvents: list[TutorProfileEventResponse] = Field(default_factory=list)
    topicEvents: list[TutorTopicEventResponse] = Field(default_factory=list)


class TutorSessionListResponse(BaseModel):
    sessions: list[TutorSessionResponse]


class TutorSessionSubjectOption(BaseModel):
    id: str
    name: str
    topics: list[PlanTopicResponse]


class TutorSessionOptionsResponse(BaseModel):
    subjects: list[TutorSessionSubjectOption]
    profiles: list[TutorProfileResponse]
