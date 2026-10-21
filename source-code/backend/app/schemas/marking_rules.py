"""Private, versioned rules applied by the server after evidence matching."""
from pydantic import BaseModel, ConfigDict, Field, model_validator


class MarkingGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=80)
    pointIds: list[str] = Field(min_length=1, max_length=200)
    maxMarks: int = Field(ge=0, le=200)
    requiredForFullCredit: list[str] = Field(default_factory=list, max_length=200)


class CombinedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phrase: str = Field(min_length=1, max_length=500)
    pointIds: list[str] = Field(min_length=2, max_length=200)


class MarkingRules(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(default=1, ge=1, le=1)
    groups: list[MarkingGroup] = Field(default_factory=list, max_length=200)
    combinedResponses: list[CombinedResponse] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def unique_groups(self):
        if len({g.id for g in self.groups}) != len(self.groups):
            raise ValueError("Scoring group identifiers must be unique")
        for g in self.groups:
            if len(set(g.pointIds)) != len(g.pointIds) or not set(g.requiredForFullCredit) <= set(g.pointIds):
                raise ValueError("A group must have unique points and its required points must belong to it")
        for rule in self.combinedResponses:
            if len(set(rule.pointIds)) != len(rule.pointIds):
                raise ValueError("A combined response must reference distinct points")
        return self
