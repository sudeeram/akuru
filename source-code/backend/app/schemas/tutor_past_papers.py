from typing import Literal
from pydantic import BaseModel, Field
from app.schemas.tutor_practice import TutorPracticeResponse


class ReleasePastPaperPart(BaseModel):
    # An empty label identifies an actual, unlettered whole question.
    partLabel: str = Field(max_length=40)
    revision: int = Field(gt=0)
    confirmSelfContained: bool
    enabled: bool = True


class PastPaperChatState(BaseModel):
    practice: TutorPracticeResponse
    paperTitle: str
    questionLabel: str
    answerRevealed: bool = False
    markingGuidance: list[dict] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    examinerAdvice: list[str] = Field(default_factory=list)
    sources: list[dict] = Field(default_factory=list)
    state: Literal['awaiting_answer', 'answered', 'revealed', 'expired']
    message: str = ''
