"""Bounded declarative matchers. No executable expressions or model decisions."""
from typing import Literal, Annotated
from pydantic import BaseModel, ConfigDict, Field, model_validator, StringConstraints

Alias=Annotated[str,StringConstraints(strip_whitespace=True,min_length=1,max_length=300)]
Unit=Annotated[str,StringConstraints(strip_whitespace=True,min_length=1,max_length=40)]

class NumericAnswer(BaseModel):
    model_config=ConfigDict(extra='forbid')
    value: str = Field(min_length=1,max_length=80)
    significantFigures: int | None = Field(default=None,ge=1,le=15)
    decimalPlaces: int | None = Field(default=None,ge=0,le=20)
    roundedFrom: bool = False
    allowPowerOfTenScaling: bool = False
    minimumSignificantFigures: int = Field(default=1,ge=1,le=15)

class MethodStep(BaseModel):
    model_config=ConfigDict(extra='forbid')
    operator: Literal['divide','multiply']
    right: str = Field(min_length=1,max_length=40)
    leftValues: list[str] = Field(default_factory=list,max_length=30)
    allowAnyLeft: bool = False

class AnswerMatcher(BaseModel):
    model_config=ConfigDict(extra='forbid')
    pointId: str = Field(min_length=1,max_length=80)
    kind: Literal['numeric','choice','set']
    answerKey: str = Field(default='',max_length=40)
    values: list[NumericAnswer] = Field(default_factory=list,max_length=50)
    requiredMembers:list[list[Alias]]=Field(default_factory=list,max_length=20)
    extraMembers:list[Alias]=Field(default_factory=list,max_length=100)
    accepted: list[Alias] = Field(default_factory=list,max_length=50)
    rejected: list[Alias] = Field(default_factory=list,max_length=100)
    incorrectValues: list[str] = Field(default_factory=list,max_length=40)
    methods: list[MethodStep] = Field(default_factory=list,max_length=10)
    units: list[Unit] = Field(default_factory=list,max_length=20)
    allowMissingUnit: bool = True

    @model_validator(mode='after')
    def typed(self):
        if self.kind=='numeric' and (not self.values and not self.methods or self.accepted or self.rejected or self.requiredMembers or self.extraMembers):
            raise ValueError('Numeric criteria need numeric values/methods, not text aliases')
        if self.kind=='set' and (not self.requiredMembers or any(not group or len(group)>20 for group in self.requiredMembers)or self.values or self.methods or self.accepted or self.rejected or self.units or self.incorrectValues):
            raise ValueError('Set matching needs bounded required-member alias groups and no unrelated criteria')
        if self.kind=='choice' and (not self.accepted or self.values or self.methods or self.units or self.requiredMembers or self.extraMembers or self.incorrectValues):
            raise ValueError('Choice criteria need reviewed aliases and no numeric rules')
        return self

class FrozenScoringPart(BaseModel):
    model_config=ConfigDict(extra='forbid')
    label:str=Field(min_length=1,max_length=40)
    marks:int=Field(ge=0,le=200)
    prompt:str=Field(max_length=12000)
    markingPoints:list[dict]=Field(min_length=1,max_length=200)
    scoringRules:dict

class DeterministicRules(BaseModel):
    model_config=ConfigDict(extra='forbid')
    engine: Literal['deterministic-v1']='deterministic-v1'
    matchers: list[AnswerMatcher] = Field(min_length=1,max_length=200)
    parts:list[FrozenScoringPart]=Field(default_factory=list,max_length=200)
    certificateId: str | None = Field(default=None,pattern=r'^[a-f0-9-]{36}$')
