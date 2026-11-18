"""Private, versioned rules applied by the server after evidence matching."""
from pydantic import BaseModel, ConfigDict, Field, model_validator, model_serializer


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


class ScoreBand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pointId: str = Field(min_length=1, max_length=80)
    marks: int = Field(ge=1, le=100)


class ScoreBandGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=80)
    bands: list[ScoreBand] = Field(min_length=2, max_length=100)


class MarkingRules(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: int = Field(default=1, ge=1, le=2)
    groups: list[MarkingGroup] = Field(default_factory=list, max_length=200)
    combinedResponses: list[CombinedResponse] = Field(default_factory=list, max_length=100)

    scoreBands: list[ScoreBandGroup] = Field(default_factory=list, max_length=100)

    @model_serializer(mode="wrap")
    def compatible_dump(self, handler):
        value = handler(self)
        if not self.scoreBands:
            value.pop("scoreBands", None)  # Preserve hashes of existing version-1 rubrics.
        return value

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
        if self.scoreBands and self.version != 2:
            raise ValueError("Score bands require rule version 2")
        if len({g.id for g in self.scoreBands}) != len(self.scoreBands):
            raise ValueError("Score-band group identifiers must be unique")
        ids = [b.pointId for g in self.scoreBands for b in g.bands]
        if len(set(ids)) != len(ids):
            raise ValueError("Each score-band point must belong to exactly one band")
        return self
