from pydantic import BaseModel, Field, model_validator


class TextbookUnitDraft(BaseModel):
    code: str = Field(min_length=1, max_length=80)
    chapter: str = Field(default="", max_length=240)
    title: str = Field(min_length=1, max_length=240)
    summary: str = Field(default="", max_length=5000)
    startPage: int = Field(ge=1)
    endPage: int = Field(ge=1)
    sections: list[str] = Field(default_factory=list, max_length=100)
    definitions: list[str] = Field(default_factory=list, max_length=100)
    concepts: list[str] = Field(default_factory=list, max_length=100)
    equations: list[str] = Field(default_factory=list, max_length=100)
    examples: list[str] = Field(default_factory=list, max_length=100)
    diagrams: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def valid_pages(self):
        if self.endPage < self.startPage:
            raise ValueError("End page must be on or after start page.")
        self.code = self.code.strip()
        self.title = self.title.strip()
        return self


class SaveTextbookReviewRequest(BaseModel):
    courseId: str
    subjectId: str
    edition: str = Field(min_length=1, max_length=80)
    units: list[TextbookUnitDraft] = Field(min_length=1, max_length=200)


class PublishTextbookRequest(BaseModel):
    confirmCourse: bool
    confirmSubject: bool
    confirmEdition: bool


class TextbookReviewResponse(BaseModel):
    versionNumber: int
    status: str
    courseId: str
    subjectId: str
    edition: str
    units: list[TextbookUnitDraft]
