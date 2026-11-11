"""Admin final-source reassessment jobs; no Student release controls."""
import uuid
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .paper_analysis import AccuracyEstimate, PartAccuracy

class AccuracyJobRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    requestId: uuid.UUID
    number: str=Field(min_length=1,max_length=40)
    expectedRevision: int=Field(ge=1)
    expectedContentHash: str=Field(pattern=r'^[a-f0-9]{64}$')
    expectedAnalysisVersion: int=Field(ge=0)

class AccuracyJobBatch(BaseModel):
    model_config=ConfigDict(extra='forbid')
    questions: list[AccuracyJobRequest]=Field(min_length=1,max_length=50)
    @model_validator(mode='after')
    def distinct(self):
        if len({v.number for v in self.questions})!=len(self.questions) or len({v.requestId for v in self.questions})!=len(self.questions):
            raise ValueError('Use distinct questions and request IDs.')
        return self

class ReviewDimensions(BaseModel):
    model_config=ConfigDict(extra='forbid')
    wording: int=Field(ge=0,le=100)
    markingPoints: int=Field(ge=0,le=100)
    visuals: int | None=Field(default=None,ge=0,le=100)

class CurriculumProposal(BaseModel):
    model_config=ConfigDict(extra="forbid")
    coverage: str=Field(pattern=r"^(supported|partial_or_uncertain|outside_current_coverage)$")
    percent: int=Field(ge=0,le=100)
    reason: str=Field(min_length=1,max_length=2000)
    chunkIds: list[str]=Field(default_factory=list,max_length=12)

class AssessedPart(PartAccuracy):
    selfContained: bool = False
    curriculum: CurriculumProposal | None = None
    dimensions: ReviewDimensions
    manualReviewReasons: list[str]=Field(default_factory=list,max_length=12)

class ModelAccuracy(BaseModel):
    model_config=ConfigDict(extra='forbid')
    question: AccuracyEstimate
    parts: list[AssessedPart]=Field(min_length=1,max_length=100)
