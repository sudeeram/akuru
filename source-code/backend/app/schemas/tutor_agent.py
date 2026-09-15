from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.tutor_sources import TutorCitation


TeachingMode = Literal[
    "explanation", "questions", "guided_practice", "socratic_practice",
    "revision", "exam_technique", "french_conversation",
]


class TutorAgentTurnRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    teachingMode: TeachingMode = "explanation"
    requestKey: str = Field(min_length=8, max_length=100)


class TutorSignalProposal(BaseModel):
    category: Literal["engagement", "confidence", "misconception", "practice_need"]
    observation: str = Field(min_length=1, max_length=300)
    evidenceRefs: list[str] = Field(min_length=1, max_length=8)
    confidence: float = Field(ge=0, le=1)


class TutorProviderOutput(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    citationRefs: list[str] = Field(default_factory=list, max_length=8)
    followUpChoices: list[str] = Field(default_factory=list, max_length=4)
    proposedSignals: list[TutorSignalProposal] = Field(default_factory=list, max_length=6)

    @field_validator("citationRefs", "followUpChoices")
    @classmethod
    def unique_values(cls, values: list[str]):
        return list(dict.fromkeys(value.strip() for value in values if value.strip()))


class TutorToolResult(BaseModel):
    name: Literal[
        "learner_context", "next_unit", "approved_source_search", "authorized_source_opening",
        "mastery_summary", "study_plan_context", "guided_practice", "deterministic_media",
    ]
    status: Literal["ready", "evidence_insufficient", "unavailable"]
    summary: str
    evidenceRefs: list[str] = Field(default_factory=list)


class TutorVisual(BaseModel):
    title: str
    altText: str
    visualType: Literal["official_source", "explanatory"]
    kind: str
    contentUrl: str | None = None
    readableFallback: str
    equation: str | None = None
    sourceLabel: str
    provenance: dict
    sourceRefs: list[str] = Field(default_factory=list)


class TutorAgentTurnResponse(BaseModel):
    operationRef: str
    turnRef: str
    content: str
    teachingMode: TeachingMode
    citations: list[TutorCitation] = Field(default_factory=list)
    followUpChoices: list[str] = Field(default_factory=list)
    toolResults: list[TutorToolResult] = Field(default_factory=list)
    visuals: list[TutorVisual] = Field(default_factory=list)
    proposedSignals: list[TutorSignalProposal] = Field(default_factory=list)
    provider: str
    model: str
    promptName: str
    promptVersion: str
