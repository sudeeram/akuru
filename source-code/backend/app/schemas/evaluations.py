import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


Category = Literal["inventory", "ocr", "equation", "diagram", "mapping", "marking", "feedback", "repeatability"]


class EvaluationCase(BaseModel):
    caseId: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9._-]+$")
    category: Category
    input: dict[str, Any] = Field(default_factory=dict)
    expected: dict[str, Any]


class CorpusCreate(BaseModel):
    subjectId: str
    name: str = Field(min_length=3, max_length=180)
    cases: list[EvaluationCase] = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def unique_cases(self):
        ids = [case.caseId for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("caseId values must be unique")
        return self


class CorpusReview(BaseModel):
    decision: Literal["approved", "retired"]


class EvaluationObservation(BaseModel):
    caseId: str
    output: dict[str, Any]


class EvaluationRunCreate(BaseModel):
    corpusId: uuid.UUID
    candidateModel: str = Field(min_length=1, max_length=120)
    promptVersion: str = Field(min_length=1, max_length=80)
    observations: list[EvaluationObservation] = Field(min_length=1, max_length=10000)


class ReleaseUpdate(BaseModel):
    subjectId: str
    workflow: Literal["assessment_feedback", "content_publication"]
    mode: Literal["review_required", "automatic"]
    runId: uuid.UUID | None = None
    confidenceThreshold: float = Field(default=0.85, ge=0, le=1)


class CorpusResponse(BaseModel):
    id: uuid.UUID
    subjectId: str
    versionNumber: int
    name: str
    cases: list[dict]
    status: str
    contentHash: str
    createdAt: datetime
    approvedAt: datetime | None


class EvaluationRunResponse(BaseModel):
    id: uuid.UUID
    corpusId: uuid.UUID
    subjectId: str
    candidateModel: str
    promptVersion: str
    metrics: dict[str, float]
    thresholds: dict[str, float]
    passed: bool
    failureReasons: list[str]
    createdAt: datetime


class ReleaseResponse(BaseModel):
    subjectId: str
    workflow: str
    mode: str
    runId: uuid.UUID | None
    confidenceThreshold: float
    activatedAt: datetime


class EvaluationDashboard(BaseModel):
    corpora: list[CorpusResponse]
    runs: list[EvaluationRunResponse]
    releases: list[ReleaseResponse]
    missingApprovedSubjects: list[str]
