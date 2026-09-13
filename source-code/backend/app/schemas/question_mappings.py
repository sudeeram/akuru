import uuid

from pydantic import BaseModel, Field, model_validator


class UnitMapping(BaseModel):
    unitId: uuid.UUID
    weight: int = Field(ge=1, le=100)
    rationale: str = Field(default="", max_length=1000)
    confidence: float | None = Field(default=None, ge=0, le=1)
    method: str | None = Field(default=None, max_length=40)


class SaveUnitMappingsRequest(BaseModel):
    mappings: list[UnitMapping] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_weights(self):
        ids = [row.unitId for row in self.mappings]
        if len(ids) != len(set(ids)):
            raise ValueError("A unit may be mapped only once.")
        if sum(row.weight for row in self.mappings) != 100:
            raise ValueError("Mapping weights must total exactly 100%.")
        return self


class UnitOption(BaseModel):
    id: str
    code: str
    title: str


class QuestionMappingResponse(BaseModel):
    questionId: str
    number: str
    prompt: str
    marks: int
    status: str
    mappings: list[UnitMapping]


class PaperMappingResponse(BaseModel):
    paperId: str
    paperTitle: str
    subjectId: str
    textbookTitle: str
    textbookEdition: str
    units: list[UnitOption]
    questions: list[QuestionMappingResponse]


class MappingSuggestionResponse(BaseModel):
    questionId: str
    method: str
    suggestions: list[UnitMapping]


class AIUnitSuggestion(BaseModel):
    unitCode: str
    weight: int = Field(ge=1, le=100)
    confidence: float = Field(ge=0, le=1)
    rationale: str = Field(min_length=1, max_length=1000)


class AIUnitSuggestionOutput(BaseModel):
    mappings: list[AIUnitSuggestion] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def total_weight(self):
        if sum(row.weight for row in self.mappings) != 100:
            raise ValueError("Suggested weights must total 100%.")
        return self
