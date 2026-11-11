"""Private, append-only analysis metadata, independent of content approval."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

SourceRole = Literal["paper", "scheme", "report"]


class AnalysisModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AnalysisProvenance(AnalysisModel):
    role: SourceRole
    method: Literal["native_pdf", "ocr", "deterministic", "codex_assisted", "openai_api", "manual", "unknown"]
    provider: str | None = Field(default=None, max_length=100)
    modelId: str | None = Field(default=None, min_length=1, max_length=160)
    modelName: str | None = Field(default=None, min_length=1, max_length=160)
    modelIdentitySource: Literal["provider_response", "operator_recorded", "not_recorded"] = "not_recorded"
    responseId: str | None = Field(default=None, max_length=200)
    guidelineId: str | None = Field(default=None, max_length=100)
    guidelineVersion: str | None = Field(default=None, max_length=80)
    promptVersion: str | None = Field(default=None, max_length=100)
    processedAt: datetime | None = None
    notes: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def identity(self):
        if self.modelId and self.method not in {"codex_assisted", "openai_api"}:
            raise ValueError("Only AI-assisted interpretation can name an AI model.")
        if self.modelId and self.modelIdentitySource == "not_recorded":
            self.modelIdentitySource = "operator_recorded"
        if self.modelIdentitySource == "provider_response" and (not self.modelId or not self.responseId):
            raise ValueError("Provider-confirmed model identity requires the model and response IDs.")
        if self.processedAt is not None and self.processedAt.tzinfo is None:
            raise ValueError("Processing time must include its timezone.")
        return self


class SourceAccuracy(AnalysisModel):
    role: SourceRole
    status: Literal["checked", "not_checked", "not_available", "no_comment"]
    percent: int | None = Field(default=None, ge=0, le=100)
    pages: list[int] = Field(default_factory=list, max_length=200)
    reasons: list[str] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def evidence(self):
        if any(page <= 0 for page in self.pages) or len(set(self.pages)) != len(self.pages):
            raise ValueError("Use distinct positive PDF page numbers.")
        if self.status in {"checked", "no_comment"} and (self.percent is None or not self.pages):
            raise ValueError("Checked sources require a confidence estimate and inspected pages.")
        if self.status in {"not_checked", "not_available"} and self.percent is not None:
            raise ValueError("Unassessed or unavailable sources cannot have an accuracy estimate.")
        if self.status == "no_comment" and self.role != "report":
            raise ValueError("Only an examiner report can have no applicable comment.")
        if any(not reason.strip() or len(reason) > 2000 for reason in self.reasons):
            raise ValueError("Provide bounded, non-empty accuracy reasons.")
        return self


class AccuracyEstimate(AnalysisModel):
    percent: int = Field(ge=0, le=100)
    reasons: list[str] = Field(min_length=1, max_length=12)
    sourceChecks: list[SourceAccuracy] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def conservative(self):
        if {source.role for source in self.sourceChecks} != {"paper", "scheme", "report"}:
            raise ValueError("Record paper, scheme and report coverage separately.")
        assessed = [source.percent for source in self.sourceChecks if source.percent is not None]
        if assessed and self.percent > min(assessed):
            raise ValueError("Overall confidence cannot exceed the weakest assessed source.")
        if any(source.status == "not_checked" for source in self.sourceChecks) and self.percent > 70:
            raise ValueError("An incomplete comparison cannot claim more than 70% confidence.")
        if any(not reason.strip() or len(reason) > 2000 for reason in self.reasons):
            raise ValueError("Provide bounded, non-empty accuracy reasons.")
        return self


class CurriculumEvidence(AnalysisModel):
    chunkId: str = Field(pattern=r"^[a-f0-9-]{36}$")
    topicRef: str = Field(min_length=1, max_length=56)
    title: str = Field(max_length=240)
    publicationId: str = Field(pattern=r"^[a-f0-9-]{36}$")
    publicationVersion: int = Field(gt=0)
    documentVersionId: str = Field(pattern=r"^[a-f0-9-]{36}$")
    page: int = Field(gt=0)
    contentHash: str = Field(pattern=r"^[a-f0-9]{64}$")


class CurriculumAssessment(AnalysisModel):
    coverage: Literal['supported', 'partial_or_uncertain', 'outside_current_coverage']
    percent: int = Field(ge=0, le=100)
    reason: str = Field(min_length=1, max_length=2000)
    policy: str = Field(max_length=80)
    evidence: list[CurriculumEvidence] = Field(default_factory=list, max_length=12)
    accepted: bool
    conflict: bool
    mappingHash: str = Field(pattern=r"^[a-f0-9]{64}$")


class PartAccuracy(AccuracyEstimate):
    label: str = Field(max_length=40)
    selfContained: bool | None = None
    curriculum: CurriculumAssessment | None = None
    provenance: list[AnalysisProvenance] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def distinct_overrides(self):
        if len({item.role for item in self.provenance}) != len(self.provenance):
            raise ValueError("Provide at most one subpart provenance override per source role.")
        return self


class RecordQuestionAnalysis(AnalysisModel):
    expectedQuestionRevision: int = Field(ge=1)
    expectedAnalysisVersion: int = Field(ge=0)
    expectedContentHash: str = Field(pattern=r"^[a-f0-9]{64}$")
    stage: Literal["extraction", "accuracy"] = "accuracy"
    methodVersion: str = Field(min_length=1, max_length=100)
    provenance: list[AnalysisProvenance] = Field(min_length=3, max_length=3)
    question: AccuracyEstimate
    parts: list[PartAccuracy] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def scopes(self):
        if len({part.label for part in self.parts}) != len(self.parts):
            raise ValueError("Record each subpart exactly once.")
        if {source.role for source in self.provenance} != {"paper", "scheme", "report"}:
            raise ValueError("Record source-specific provenance for paper, scheme and report.")
        return self


class QuestionAnalysisResponse(BaseModel):
    id: str
    version: int
    stage: Literal["extraction", "accuracy"]
    questionRevision: int
    contentHash: str
    sourceManifest: list[dict]
    methodVersion: str
    provenance: list[AnalysisProvenance]
    question: AccuracyEstimate
    parts: list[PartAccuracy]
    createdAt: datetime
    isCurrent: bool
