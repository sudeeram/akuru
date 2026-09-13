from typing import Literal
import uuid

from pydantic import BaseModel, Field, model_validator


class SourceLocation(BaseModel):
    page: int = Field(gt=0)
    blockId: uuid.UUID
    boundingBox: dict = Field(default_factory=dict)


class OfficialQuestionReview(BaseModel):
    number: str = Field(min_length=1, max_length=40)
    parentNumber: str | None = Field(default=None, max_length=40)
    prompt: str = Field(min_length=1)
    sharedStem: str = ""
    marks: int = Field(gt=0, le=200)
    equations: list[str] = Field(default_factory=list)
    assetIds: list[uuid.UUID] = Field(min_length=1)
    sourceLocations: list[SourceLocation] = Field(min_length=1)


class MarkingPoint(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    text: str = Field(min_length=1)
    kind: Literal["method", "accuracy", "independent", "communication", "other"] = "other"


class MarkSchemeEntryReview(BaseModel):
    questionNumber: str = Field(min_length=1, max_length=40)
    maxMarks: int = Field(gt=0, le=200)
    markingPoints: list[MarkingPoint] = Field(min_length=1)
    alternatives: list[str] = Field(default_factory=list)
    sourceLocations: list[SourceLocation] = Field(min_length=1)


class ExaminerCommentReview(BaseModel):
    questionNumber: str = Field(min_length=1, max_length=40)
    commonMistakes: list[str] = Field(default_factory=list)
    advice: list[str] = Field(default_factory=list)
    sourceLocations: list[SourceLocation] = Field(min_length=1)


class OfficialMaterialReview(BaseModel):
    versionNumber: int
    status: str
    kind: Literal["past_paper", "mark_scheme", "examiner_report"]
    courseId: str
    subjectId: str
    sourcePaperId: str | None = None
    sourcePaperVersionId: str | None = None
    expectedItemCount: int = Field(ge=0, le=1000)
    completenessConfirmed: bool = False
    questions: list[OfficialQuestionReview] = Field(default_factory=list)
    markSchemeEntries: list[MarkSchemeEntryReview] = Field(default_factory=list)
    examinerComments: list[ExaminerCommentReview] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_numbers(self):
        values = (
            [row.number for row in self.questions]
            if self.kind == "past_paper" else
            [row.questionNumber for row in self.markSchemeEntries]
            if self.kind == "mark_scheme" else
            [row.questionNumber for row in self.examinerComments]
        )
        if len(values) != len(set(values)):
            raise ValueError("Question numbers must be unique within a material version.")
        return self


class SaveOfficialMaterialReview(BaseModel):
    expectedItemCount: int = Field(ge=0, le=1000)
    completenessConfirmed: bool = False
    questions: list[OfficialQuestionReview] = Field(default_factory=list, max_length=1000)
    markSchemeEntries: list[MarkSchemeEntryReview] = Field(default_factory=list, max_length=1000)
    examinerComments: list[ExaminerCommentReview] = Field(default_factory=list, max_length=1000)

    @model_validator(mode="after")
    def unique_numbers(self):
        for rows, attribute in ((self.questions, "number"), (self.markSchemeEntries, "questionNumber"), (self.examinerComments, "questionNumber")):
            values = [getattr(row, attribute) for row in rows]
            if len(values) != len(set(values)):
                raise ValueError("Question numbers must be unique within a material version.")
        return self


class PublishOfficialMaterialRequest(BaseModel):
    confirmCourse: bool
    confirmSubject: bool
    confirmSourcePaper: bool = False
    confirmComplete: bool
