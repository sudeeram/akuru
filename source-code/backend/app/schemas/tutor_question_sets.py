from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class FormativePoint(BaseModel):
    model_config = ConfigDict(extra='forbid')
    code: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=1, max_length=1500)


class GeneratedPracticeItem(BaseModel):
    model_config = ConfigDict(extra='forbid')
    prompt: str = Field(min_length=10, max_length=2500)
    marks: int = Field(ge=1, le=6)
    markingPoints: list[FormativePoint] = Field(min_length=1, max_length=8)
    suggestedAnswer: str = Field(min_length=10, max_length=2500)
    topicRefs: list[str] = Field(min_length=1, max_length=4)
    difficulty: Literal['easy', 'medium', 'difficult']
    requiresVisual: bool


class GeneratedPracticeCheck(BaseModel):
    model_config = ConfigDict(extra='forbid')
    scientificallyCorrect: bool
    solvableFromQuestion: bool
    rubricConsistent: bool
    topicGrounded: bool
    originalWording: bool
    reason: str = Field(max_length=1200)


class FormativeMatch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    pointId: str = Field(min_length=1, max_length=80)
    matched: bool
    evidence: str = Field(max_length=2000)
    reason: str = Field(min_length=1, max_length=1500)


class FormativeFeedback(BaseModel):
    model_config = ConfigDict(extra='forbid')
    matches: list[FormativeMatch] = Field(max_length=100)
    correctPoints: list[str] = Field(max_length=12)
    mistakes: list[str] = Field(max_length=12)
    omissions: list[str] = Field(max_length=12)
    improvedAnswer: str = Field(min_length=1, max_length=5000)
    explanation: str = Field(min_length=1, max_length=4000)
    uncertainty: str = Field(max_length=1500)


class TutorQuestionSetState(BaseModel):
    setRef: str
    status: Literal['active', 'completed', 'abandoned']
    sourceKind: Literal['official', 'generated']
    requestedCount: int
    availableCount: int
    position: int
    completedCount: int
    topicTitles: list[str]
    question: dict | None = None
    feedback: dict | None = None
    answer: str | None = None
    itemStatus: str
    assisted: bool
    processing: bool = False
    message: str = ''
    summary: dict = Field(default_factory=dict)
