"""Admin-only, unpublished question-by-question review contracts."""
from typing import Literal
import uuid

from pydantic import BaseModel, Field, model_validator
from app.schemas.marking_rules import MarkingRules
from app.schemas.answer_visuals import AnswerVisual
from app.schemas.paper_analysis import AnalysisProvenance, QuestionAnalysisResponse


ReviewStatus = Literal["unreviewed", "needs_correction", "ready_for_approval", "approved", "ai_approved", "excluded"]
CoverageStatus = Literal["unreviewed", "supported", "partial_or_uncertain", "outside_current_coverage"]


class ReviewEvidence(BaseModel):
    page: int = Field(gt=0)
    blockId: uuid.UUID | None = None
    assetId: uuid.UUID | None = None


class ReviewMarkingPoint(BaseModel):
    code: str = Field(default="", max_length=30)
    text: str = Field(default="", max_length=2000)
    kind: Literal["method", "accuracy", "independent", "communication", "other"] = "other"
    dependsOn: str | None = Field(default=None, max_length=30)
    followThrough: bool = False
    acceptedAnswers: list[str] = Field(default_factory=list, max_length=30)


class TextbookPageEvidence(BaseModel):
    topicRef: str = Field(min_length=1, max_length=56)
    documentVersionId: uuid.UUID
    page: int = Field(gt=0)
    printedPageLabel: str = Field(min_length=1, max_length=40)


class ExtractionConfidence(BaseModel):
    percent: int = Field(ge=0, le=100)
    methodVersion: str = Field(min_length=1, max_length=80)
    reasons: list[str] = Field(default_factory=list, max_length=12)


class ReviewPart(BaseModel):
    label: str = Field(default="", max_length=40)
    marks: int = Field(ge=0, le=200)
    prompt: str = Field(default="", max_length=12000)
    visualAssetIds: list[uuid.UUID] = Field(default_factory=list)
    answerVisuals: list[AnswerVisual] = Field(default_factory=list, max_length=30)
    answerVisualRequired: bool = False
    responseType: Literal["text", "drawing"] = "text"
    markingPoints: list[ReviewMarkingPoint] = Field(default_factory=list, max_length=200)
    alternatives: list[str] = Field(default_factory=list, max_length=100)
    examinerAdvice: str = Field(default="", max_length=12000)
    paperSources: list[ReviewEvidence] = Field(default_factory=list)
    schemeSources: list[ReviewEvidence] = Field(default_factory=list)
    reportSources: list[ReviewEvidence] = Field(default_factory=list)
    scoringRules: MarkingRules = Field(default_factory=MarkingRules)
    assessmentReadiness: Literal["unreviewed", "automatic", "manual_only"] = "unreviewed"
    assessmentReadinessReason: str = Field(default="", max_length=4000)
    coverage: CoverageStatus = "unreviewed"
    topicRefs: list[str] = Field(default_factory=list)
    textbookEvidence: list[TextbookPageEvidence] = Field(default_factory=list, max_length=100)
    coverageReason: str = Field(default="", max_length=4000)
    status: ReviewStatus = "unreviewed"
    extractionConfidence: ExtractionConfidence | None = None


class ReviewQuestionData(BaseModel):
    marks: int = Field(ge=0, le=200)
    sharedStem: str = Field(default="", max_length=12000)
    prompt: str = Field(default="", max_length=30000)
    paperSources: list[ReviewEvidence] = Field(default_factory=list)
    visualAssetIds: list[uuid.UUID] = Field(default_factory=list)
    candidateVisualAssetIds: list[uuid.UUID] = Field(default_factory=list)
    visualAltText: str = Field(default="", max_length=2000)
    parts: list[ReviewPart] = Field(min_length=1, max_length=100)
    exclusionReason: str = Field(default="", max_length=4000)
    extractionConfidence: ExtractionConfidence | None = None

    @model_validator(mode="after")
    def reconcile(self):
        if len({part.label for part in self.parts}) != len(self.parts):
            raise ValueError("Subpart labels must be unique")
        return self


class StartPaperReview(BaseModel):
    schemeDocumentId: uuid.UUID | None = None
    reportDocumentId: uuid.UUID | None = None
    expectedQuestionCount: int = Field(default=0, ge=0, le=200)


class SaveReviewQuestion(BaseModel):
    expectedRevision: int = Field(ge=0)
    number: str = Field(min_length=1, max_length=40)
    status: ReviewStatus = "unreviewed"
    data: ReviewQuestionData


class SeedPartProposal(BaseModel):
    """Private draft fields only; approval and scoring readiness are server-owned."""
    model_config = {"extra": "forbid"}
    markingPoints: list[ReviewMarkingPoint] = Field(default_factory=list, max_length=200)
    responseType: Literal["text", "drawing"] = "text"
    assessmentReadinessReason: str = Field(default="Native proposal; review exact scoring rules before release.", max_length=4000)
    coverageReason: str = Field(default="Topic mapping has not been reviewed.", max_length=4000)


class SeedPaperReview(BaseModel):
    draftBank: dict
    coverageTriage: dict | None = None
    provenance: list[AnalysisProvenance] = Field(default_factory=list, max_length=3)

    @model_validator(mode="before")
    @classmethod
    def batch_provenance(cls, value):
        if isinstance(value, dict) and not value.get("provenance"):
            batch = value.get("draftBank")
            if isinstance(batch, dict) and batch.get("provenance") is not None:
                return {**value, "provenance": batch["provenance"]}
        return value

    @model_validator(mode="after")
    def distinct_provenance(self):
        if len({item.role for item in self.provenance}) != len(self.provenance):
            raise ValueError("Provide at most one provenance record per source role.")
        return self


class CreateReviewCrop(BaseModel):
    source: Literal["paper", "scheme"] = "paper"
    page: int = Field(gt=0)
    kind: Literal["diagram", "table"]
    x0: float = Field(ge=0, lt=1)
    y0: float = Field(ge=0, lt=1)
    x1: float = Field(gt=0, le=1)
    y1: float = Field(gt=0, le=1)
    altText: str = Field(min_length=10, max_length=2000)


class ReviewCropResponse(BaseModel):
    assetId: uuid.UUID
    page: int
    kind: Literal["diagram", "table"]
    altText: str
    approved: bool = True
    bounds: dict[str, float] = Field(default_factory=dict)


class ReviewQuestionResponse(BaseModel):
    number: str
    revision: int
    status: ReviewStatus
    data: ReviewQuestionData
    reviewedBy: str | None = None
    reviewedAt: str | None = None
    analysisContentHash: str | None = None
    analysisVersion: int = 0
    accuracyAnalysis: QuestionAnalysisResponse | None = None
    extractionAnalysis: QuestionAnalysisResponse | None = None


class PaperReviewResponse(BaseModel):
    paperDocumentId: str
    paperVersionId: str
    schemeDocumentId: str | None
    reportDocumentId: str | None
    expectedQuestionCount: int
    questionCount: int
    approvedCount: int
    wholePaperReady: bool
    assessmentReleaseReady: bool = False
    automaticAssessmentReady: bool = False
    assessmentBlockers: list[str] = Field(default_factory=list)
    blockers: list[str]
    questions: list[ReviewQuestionResponse]


class AutoApprovalResult(BaseModel):
    number: str
    status: ReviewStatus
    changed: bool
    reason: str


class PaperAutoApprovalResponse(BaseModel):
    policy: str
    thresholdExclusive: int
    results: list[AutoApprovalResult]
