"""Prepared review data only: no code, provider instructions or client verdicts."""
import uuid
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator
from .official_paper_reviews import ReviewPart
from .paper_analysis import PartAccuracy,AnalysisProvenance,AccuracyEstimate

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid')

class PartCorrection(Strict):
    partLabel:str=Field(min_length=1,max_length=40)
    expectedScopeHash:str=Field(pattern=r'^[a-f0-9]{64}$')
    fields:dict=Field(default_factory=dict,max_length=20)
    sourceFinding:PartAccuracy|None=None
    @model_validator(mode='after')
    def allowed_fields(self):
        allowed=set(ReviewPart.model_fields)-{'label','status','assessmentReadiness','assessmentReadinessReason','extractionConfidence'}
        if set(self.fields)-allowed:raise ValueError('Only typed content, evidence, mapping and rubric corrections are permitted')
        if self.sourceFinding and self.sourceFinding.label!=self.partLabel:raise ValueError('Finding label must match the corrected part')
        return self

class IssueDecision(Strict):
    issueId:str=Field(pattern=r'^[a-f0-9]{64}$')
    partLabel:str|None=Field(default=None,max_length=40)
    disposition:Literal['corrected_and_rechecked','scheme_precedence','report_guidance_excluded','publisher_ambiguity_adjudicated','still_unresolved']
    note:str=Field(min_length=10,max_length=2000)

class VisualDecision(Strict):
    assetId:uuid.UUID
    expectedSha256:str=Field(pattern=r'^[a-f0-9]{64}$')
    sourceRole:Literal['paper','scheme']='paper'
    partLabel:str|None=Field(default=None,max_length=40)
    decision:Literal['approve','reject']
    caption:str=Field(default='',max_length=2000)
    altText:str=Field(min_length=10,max_length=2000)

class StageReview(Strict):
    schemaVersion:Literal[1]=1
    requestId:uuid.UUID
    number:str=Field(min_length=1,max_length=40)
    expectedRevision:int=Field(ge=1)
    expectedContentHash:str=Field(pattern=r'^[a-f0-9]{64}$')
    expectedAnalysisVersion:int=Field(ge=0)
    provenance:list[AnalysisProvenance]=Field(min_length=3,max_length=3)
    reason:str=Field(min_length=10,max_length=2000)
    corrections:list[PartCorrection]=Field(min_length=1,max_length=100)
    questionFinding:AccuracyEstimate|None=None
    sharedFields:dict=Field(default_factory=dict,max_length=4)
    visualDecisions:list[VisualDecision]=Field(default_factory=list,max_length=100)
    issueDecisions:list[IssueDecision]=Field(default_factory=list,max_length=100)
    reopenApproved:bool=False
    @model_validator(mode='after')
    def distinct(self):
        if set(self.sharedFields)-{'sharedStem','visualAssetIds','candidateVisualAssetIds','visualAltText'}:raise ValueError('Only explicit shared context/visual fields can be amended')
        if len({x.assetId for x in self.visualDecisions})!=len(self.visualDecisions):raise ValueError('Review each visual once')
        if len({x.partLabel for x in self.corrections})!=len(self.corrections):raise ValueError('Choose each subpart once')
        if {p.role for p in self.provenance}!={'paper','scheme','report'}:raise ValueError('Record paper/scheme/report provenance')
        return self

class ApplyReview(Strict):
    requestId:uuid.UUID
    expectedPreviewHash:str=Field(pattern=r'^[a-f0-9]{64}$')
    evaluateApproval:bool=True
    releaseTutor:bool=False

class ScopedApproval(Strict):
    requestId:uuid.UUID
    expectedRevision:int=Field(ge=1)
    partLabels:list[str]=Field(default_factory=list,max_length=100)
    dryRun:bool=False

class ReleaseValidation(Strict):
    target:Literal['tutor_practice','official_drafts','formal_exam']
    numbers:list[str]=Field(default_factory=list,max_length=100)

class ReviewBatch(Strict):
    requestId:uuid.UUID
    items:list[uuid.UUID]=Field(min_length=1,max_length=50)
    previewHashes:dict[str,str]=Field(max_length=50)
    stopOnConflict:bool=True
    evaluateApproval:bool=True
    releaseTutor:bool=False

    @model_validator(mode='after')
    def bounded_unique_items(self):
        import re
        if len(set(self.items)) != len(self.items):raise ValueError('Choose each change set once')
        if set(self.previewHashes) != {str(item) for item in self.items}:raise ValueError('Supply exactly one preview hash for each change set')
        if any(not re.fullmatch(r'[a-f0-9]{64}', value) for value in self.previewHashes.values()):raise ValueError('Invalid preview hash')
        return self
