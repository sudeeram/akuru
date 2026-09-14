from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.curriculum_plans import PlanUnitResponse
from app.schemas.tutor_profiles import TutorProfileResponse


class TutorSessionStartRequest(BaseModel):
    subjectId: str = Field(min_length=2, max_length=32)
    unitId: str = Field(min_length=32, max_length=40)
    profileRef: str = Field(min_length=8, max_length=48)
    requestKey: str = Field(min_length=8, max_length=100)


class TutorTurnCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    modality: Literal["text", "voice"] = "text"
    requestKey: str = Field(min_length=8, max_length=100)


class TutorSwitchProfileRequest(BaseModel):
    profileRef: str = Field(min_length=8, max_length=48)
    requestKey: str = Field(min_length=8, max_length=100)


class TutorSwitchUnitRequest(BaseModel):
    unitId: str = Field(min_length=32, max_length=40)
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
    createdAt: datetime


class TutorProfileEventResponse(BaseModel):
    fromProfileRef: str
    fromProfileVersion: int
    toProfileRef: str
    toProfileVersion: int
    handoverSummary: dict
    createdAt: datetime


class TutorUnitEventResponse(BaseModel):
    fromUnit: PlanUnitResponse
    toUnit: PlanUnitResponse
    createdAt: datetime


class TutorSessionResponse(BaseModel):
    sessionRef: str
    subjectId: str
    activeUnit: PlanUnitResponse
    currentTutor: TutorProfileResponse
    mode: Literal["practice"]
    status: Literal["active", "ended"]
    startedAt: datetime
    endedAt: datetime | None = None
    turns: list[TutorTurnResponse] = Field(default_factory=list)
    profileEvents: list[TutorProfileEventResponse] = Field(default_factory=list)
    unitEvents: list[TutorUnitEventResponse] = Field(default_factory=list)


class TutorSessionListResponse(BaseModel):
    sessions: list[TutorSessionResponse]


class TutorSessionSubjectOption(BaseModel):
    id: str
    name: str
    units: list[PlanUnitResponse]


class TutorSessionOptionsResponse(BaseModel):
    subjects: list[TutorSessionSubjectOption]
    profiles: list[TutorProfileResponse]
