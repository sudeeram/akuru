from pydantic import BaseModel, Field


class PlanUnitResponse(BaseModel):
    id: str
    code: str
    title: str


class PlanPeriod(BaseModel):
    grade: int = Field(ge=10, le=11)
    term: int = Field(ge=1, le=3)
    unitIds: list[str] = Field(default_factory=list, max_length=300)


class SavePlanRequest(BaseModel):
    periods: list[PlanPeriod] = Field(min_length=1, max_length=6)


class PublishPlanRequest(BaseModel):
    confirmSubject: bool
    confirmTextbook: bool


class CurriculumPlanResponse(BaseModel):
    versionNumber: int
    status: str
    subjectId: str
    textbookTitle: str
    textbookEdition: str
    availableUnits: list[PlanUnitResponse]
    periods: list[PlanPeriod]


class CoverageDiagnosticResponse(BaseModel):
    status: str
    message: str
    planVersion: int | None = None
    currentGrade: int | None = None
    currentTerm: int | None = None
    coveredUnits: list[PlanUnitResponse] = Field(default_factory=list)
    missingPeriods: list[str] = Field(default_factory=list)


class QuestionPoolDiagnosticResponse(BaseModel):
    status: str
    message: str
    planVersion: int | None = None
    eligibleQuestionCount: int = 0
    eligibleMarks: int = 0
    requestedQuestionCount: int = 0
    requestedMarks: int = 0
    shortageQuestionCount: int = 0
    shortageMarks: int = 0
