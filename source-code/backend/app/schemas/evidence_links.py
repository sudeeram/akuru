"""Private, source-version-bound exact evidence proposals."""
import uuid
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.paper_analysis import AnalysisProvenance

class Region(BaseModel):
    model_config = ConfigDict(extra='forbid')
    x0: float = Field(ge=0, lt=1)
    y0: float = Field(ge=0, lt=1)
    x1: float = Field(gt=0, le=1)
    y1: float = Field(gt=0, le=1)
    @model_validator(mode='after')
    def positive(self):
        if self.x1<=self.x0 or self.y1<=self.y0:
            raise ValueError('Select a region with positive width and height.')
        return self

class EvidenceSelection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    part: str = Field(max_length=40)
    role: Literal['paper','scheme']
    page: int = Field(gt=0)
    blockId: uuid.UUID | None = None
    bounds: Region | None = None
    reason: str = Field(min_length=10,max_length=2000)
    confidence: int = Field(ge=0,le=100)
    sourceVerified: bool = False
    @model_validator(mode='after')
    def location(self):
        if (self.blockId is None)==(self.bounds is None):
            raise ValueError('Choose either an existing block or an original PDF region.')
        return self

class ProposeEvidenceLinks(BaseModel):
    model_config = ConfigDict(extra='forbid')
    requestId: uuid.UUID
    number: str = Field(min_length=1,max_length=40)
    expectedRevision: int = Field(ge=1)
    expectedContentHash: str = Field(pattern=r'^[a-f0-9]{64}$')
    selections: list[EvidenceSelection] = Field(default_factory=list,max_length=150)
    provenance: list[AnalysisProvenance] = Field(default_factory=list,max_length=2)
    @model_validator(mode='after')
    def source_identity(self):
        if len({p.role for p in self.provenance})!=len(self.provenance) or any(p.role=='report' for p in self.provenance):
            raise ValueError('Use distinct paper/scheme provenance.')
        if self.selections:
            for role in {s.role for s in self.selections}:
                p=next((p for p in self.provenance if p.role==role),None)
                if not p or p.method not in {'manual','codex_assisted','openai_api'}:
                    raise ValueError('Imported selections require source-specific manual or AI provenance.')
                if p.method in {'codex_assisted','openai_api'} and not p.modelId:
                    raise ValueError('Record the actual model for AI-assisted selections.')
        return self

class ReviewEvidenceLinks(BaseModel):
    model_config = ConfigDict(extra='forbid')
    proposalIds: list[uuid.UUID] = Field(min_length=1,max_length=150)
    expectedRevision: int = Field(ge=1)
    expectedContentHash: str = Field(pattern=r'^[a-f0-9]{64}$')
    decision: Literal['apply','reject']
    confirmSourceReview: bool = False
    autoOnly: bool = False

class EvidenceBatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    questions: list[ProposeEvidenceLinks] = Field(min_length=1,max_length=50)
    @model_validator(mode='after')
    def distinct(self):
        if len({q.number for q in self.questions})!=len(self.questions) or len({q.requestId for q in self.questions})!=len(self.questions):
            raise ValueError('Choose distinct questions and request IDs.')
        return self
