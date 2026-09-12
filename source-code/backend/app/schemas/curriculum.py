from pydantic import BaseModel


class CourseResponse(BaseModel):
    id: str
    name: str
    phase1Active: bool


class SubjectResponse(BaseModel):
    id: str
    name: str


class CatalogResponse(BaseModel):
    courses: list[CourseResponse]
    subjects: list[SubjectResponse]
