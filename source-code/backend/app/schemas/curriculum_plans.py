from pydantic import BaseModel, Field


class PlanTopicResponse(BaseModel):
    topicRef: str
    code: str
    title: str
    groupRef: str
    groupCode: str
    groupTitle: str


class PlanTopicGroupResponse(BaseModel):
    groupRef: str
    code: str
    title: str
    topics: list[PlanTopicResponse]


class PlanPeriod(BaseModel):
    grade: int = Field(ge=10, le=11)
    term: int = Field(ge=1, le=3)
    topicRefs: list[str] = Field(default_factory=list, max_length=500)


class PlanChangeResponse(BaseModel):
    topicRef: str
    code: str
    title: str
    change: str
    fromPeriod: str | None = None
    toPeriod: str | None = None


class SavePlanRequest(BaseModel):
    periods: list[PlanPeriod] = Field(min_length=1, max_length=6)


class PublishPlanRequest(BaseModel):
    confirmSubject: bool
    confirmTextbook: bool
    confirmPublishedChanges: bool = False


class CurriculumPlanResponse(BaseModel):
    versionNumber: int
    status: str
    subjectId: str
    textbookTitle: str
    textbookEdition: str
    groupLabel: str = "unit"
    groups: list[PlanTopicGroupResponse] = Field(default_factory=list)
    periods: list[PlanPeriod]
    publishedPeriods: list[PlanPeriod] = Field(default_factory=list)
    changes: list[PlanChangeResponse] = Field(default_factory=list)
    requiresPublishedChangeConfirmation: bool = False
    basedOnVersion: int | None = None
    createdAt: str | None = None
    publishedAt: str | None = None


class CoverageDiagnosticResponse(BaseModel):
    status: str
    message: str
    planVersion: int | None = None
    currentGrade: int | None = None
    currentTerm: int | None = None
    coveredTopics: list[PlanTopicResponse] = Field(default_factory=list)
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
