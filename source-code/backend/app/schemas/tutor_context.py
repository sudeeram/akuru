from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.curriculum_plans import PlanUnitResponse


class LearnerContextRequest(BaseModel):
    requestKey: str = Field(min_length=8, max_length=100)


class ContextEvidence(BaseModel):
    ref: str
    kind: Literal["mastery_event", "assessment_result", "mistake", "study_plan_item"]
    observedAt: datetime
    summary: str


class ContextStatement(BaseModel):
    text: str
    signal: Literal["strong", "weak", "improving", "declining", "low_confidence", "insufficient_evidence", "recurring_mistake", "planned_activity"]
    evidenceRefs: list[str]
    cautious: bool


class ContextAttempt(BaseModel):
    evidenceRef: str
    observedAt: datetime
    mode: str
    score: float
    awardedMarks: int
    maxMarks: int
    markingSummary: list[str]


class ContextMistakePattern(BaseModel):
    topic: str
    category: str
    last7Days: int
    last30Days: int
    lifetime: int
    evidenceRefs: list[str]
    statement: ContextStatement


class ContextPlanItem(BaseModel):
    evidenceRef: str
    title: str
    activityType: str
    status: str
    scheduledFor: datetime


class ContextUnit(BaseModel):
    unit: PlanUnitResponse
    active: bool
    masteryScore: float | None = None
    confidence: str | None = None
    trend: float | None = None
    evidenceCount: int = 0
    varietyCount: int = 0
    dimensions: dict[str, float] = Field(default_factory=dict)
    signals: list[str] = Field(default_factory=list)
    statements: list[ContextStatement] = Field(default_factory=list)
    attempts: list[ContextAttempt] = Field(default_factory=list)
    mistakes: list[ContextMistakePattern] = Field(default_factory=list)
    studyPlan: list[ContextPlanItem] = Field(default_factory=list)


class ProviderLearnerContext(BaseModel):
    learnerRef: str
    subjectId: str
    activeUnitCode: str
    contextVersion: str
    learningSignals: list[dict]
    recurringMistakes: list[dict]
    plannedActivities: list[dict]


class LearnerContextResponse(BaseModel):
    operationRef: str
    contextVersion: str
    generatedAt: datetime
    subjectId: str
    activeUnit: PlanUnitResponse
    units: list[ContextUnit]
    evidence: list[ContextEvidence]
    providerContext: ProviderLearnerContext
