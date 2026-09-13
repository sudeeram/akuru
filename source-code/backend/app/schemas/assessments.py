import uuid
from datetime import datetime
from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class AssessmentMode(StrEnum):
    PRACTICE = "practice"
    OFFICIAL_PAPER = "official_paper"
    MOCK = "mock"

class BlueprintCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    subjectId: str
    grade: Literal[10, 11]
    term: Literal[1, 2, 3]
    mode: Literal["mock"] = "mock"
    targetMarks: int = Field(gt=0, le=300)
    durationMinutes: int = Field(gt=0, le=300)
    questionCount: int = Field(gt=0, le=100)
    skills: list[str] = Field(default_factory=list, max_length=30)
    difficultyProfile: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def valid_difficulty(self):
        if any(key not in {"foundation", "standard", "stretch", "mixed"} or value < 0 for key, value in self.difficultyProfile.items()):
            raise ValueError("Difficulty profile may contain non-negative foundation, standard, stretch or mixed counts only.")
        if self.difficultyProfile and sum(self.difficultyProfile.values()) != self.questionCount:
            raise ValueError("Difficulty profile counts must equal questionCount.")
        return self

class BlueprintResponse(BlueprintCreate):
    id: uuid.UUID
    status: str

class AssessmentStart(BaseModel):
    mode: AssessmentMode
    subjectId: str
    blueprintId: uuid.UUID | None = None
    paperId: uuid.UUID | None = None

class AnswerSave(BaseModel):
    questionId: uuid.UUID
    answer: str = Field(default="", max_length=100_000)
    fileId: str | None = Field(default=None, max_length=120)
    idempotencyKey: str = Field(min_length=8, max_length=100)

class SubmissionRequest(BaseModel):
    idempotencyKey: str = Field(min_length=8, max_length=100)

class AssessmentQuestionResponse(BaseModel):
    id: uuid.UUID
    number: str
    prompt: str
    sharedStem: str
    marks: int
    equations: list
    assetIds: list
    sourceLocations: list
    unitIds: list
    skills: list
    difficulty: str
    answer: str = ""
    fileId: str | None = None
    saveRevision: int = 0
    rubric: dict | None = None

class AssessmentResponse(BaseModel):
    id: uuid.UUID
    studentId: uuid.UUID
    subjectId: str
    mode: str
    status: str
    title: str
    targetMarks: int
    durationMinutes: int
    startedAt: datetime
    endsAt: datetime
    submittedAt: datetime | None
    skills: list
    difficultyProfile: dict
    feedbackVisible: bool
    questions: list[AssessmentQuestionResponse]

class AssessmentListResponse(BaseModel):
    assessments: list[AssessmentResponse]
