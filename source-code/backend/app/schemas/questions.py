from pydantic import BaseModel, Field


class QuestionReference(BaseModel):
    questionId: str
    marks: int = Field(gt=0)
