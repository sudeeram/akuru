from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.auth import UserResponse


class ProgressionResponse(BaseModel):
    grade: str
    term: str


class SubjectCourseResponse(BaseModel):
    level: str
    syllabus: str


class StudentResponse(BaseModel):
    id: str
    username: str
    name: str
    initial: str
    parentId: str
    level: str
    grade: str
    term: str
    progression: list[ProgressionResponse]
    subjects: list[str]
    courses: dict[str, SubjectCourseResponse]
    needsConfiguration: bool


class AccountSummaryResponse(BaseModel):
    id: str
    username: str
    name: str
    role: Literal["parent", "student"]


class SubjectPresentationResponse(BaseModel):
    id: str
    name: str
    symbol: str
    color: str
    topic: str
    topics: list[str]
    course: str


class ProgressionPairResponse(BaseModel):
    grade: str
    term: str


class PortalCatalogResponse(BaseModel):
    courses: list[str]
    activeCourses: list[str]
    grades: list[str]
    terms: list[str]
    kinds: list[str]
    progressionPairs: list[ProgressionPairResponse]


class PortalStateResponse(BaseModel):
    user: UserResponse
    catalog: PortalCatalogResponse
    accounts: list[AccountSummaryResponse]
    subjects: list[SubjectPresentationResponse]
    students: list[StudentResponse]
    units: list[dict[str, Any]] = Field(default_factory=list)
    coverage: list[dict[str, Any]] = Field(default_factory=list)
    questionBank: list[dict[str, Any]] = Field(default_factory=list)
    drafts: dict[str, Any] = Field(default_factory=dict)
    questions: list[dict[str, Any]] = Field(default_factory=list)
    attempts: list[dict[str, Any]] = Field(default_factory=list)
    assignments: list[dict[str, Any]] = Field(default_factory=list)
    documents: list[dict[str, Any]] = Field(default_factory=list)
    exams: list[dict[str, Any]] = Field(default_factory=list)
    assessmentBlueprints: list[dict[str, Any]] = Field(default_factory=list)
    officialPapers: list[dict[str, Any]] = Field(default_factory=list)
    reviews: list[dict[str, Any]] = Field(default_factory=list)
    plans: dict[str, Any] = Field(default_factory=dict)
    mastery: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    recommendations: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


class UiFeaturesUserResponse(BaseModel):
    name: str
    role: Literal["admin"]


class UiFeaturesResponse(BaseModel):
    allowed: Literal[True]
    user: UiFeaturesUserResponse
