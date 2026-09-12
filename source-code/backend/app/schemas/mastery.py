from pydantic import BaseModel, Field


class MasteryScore(BaseModel):
    score: float = Field(ge=0, le=10)
    confidence: str
