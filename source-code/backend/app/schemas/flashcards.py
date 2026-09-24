from typing import Literal

from pydantic import BaseModel, Field, model_validator


class FlashcardGenerateRequest(BaseModel):
    topicRef: str = Field(min_length=8, max_length=80)
    cardLimit: int = Field(default=12, ge=3, le=40)
    requestKey: str = Field(min_length=8, max_length=100)


class FlashcardCardUpdateRequest(BaseModel):
    front: str = Field(min_length=2, max_length=500)
    back: str = Field(min_length=2, max_length=3000)
    decision: Literal["review_required", "approved", "rejected"]

    @model_validator(mode="after")
    def clean(self):
        self.front = " ".join(self.front.split())
        self.back = " ".join(self.back.split())
        return self


class FlashcardSessionStartRequest(BaseModel):
    requestKey: str = Field(min_length=8, max_length=100)
    mode: Literal["quick", "normal", "full_topic", "difficult", "due_today", "unit_mixed"] = "normal"


class FlashcardRatingRequest(BaseModel):
    rating: Literal["again", "difficult", "good", "easy"]
    requestKey: str = Field(min_length=8, max_length=100)


class FlashcardWithdrawRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


class FlashcardCardResponse(BaseModel):
    cardRef: str
    ordinal: int
    version: int
    front: str
    back: str | None = None
    status: str
    warnings: list[str]
    source: dict
    conceptKey: str = ""
    category: str = "essential_knowledge"
    variationType: str = "recall"
    difficulty: str = "core"


class FlashcardDeckResponse(BaseModel):
    deckRef: str
    topicRef: str
    topicCode: str
    topicTitle: str
    groupCode: str
    groupTitle: str
    subjectId: str
    title: str
    status: str
    contentVersion: int
    cardCount: int
    approvedCount: int
    reviewRequiredCount: int
    rejectedCount: int
    cards: list[FlashcardCardResponse] = Field(default_factory=list)
    releasedAt: str | None = None
    releaseId: str | None = None
    artifactChecksum: str | None = None
    validationStatus: str | None = None
    categoryDistribution: dict[str, int] = Field(default_factory=dict)
    validationSummary: dict = Field(default_factory=dict)


class FlashcardSessionResponse(BaseModel):
    sessionRef: str
    deck: FlashcardDeckResponse
    status: str
    currentOrdinal: int
    reviewedCount: int
    totalCards: int
    currentCard: FlashcardCardResponse | None
    answerRevealed: bool = False
    schedulerVersion: str
    message: str
    mode: str = "full_topic"
    selectionReasons: list[str] = Field(default_factory=list)


class FlashcardStudyOption(BaseModel):
    mode: Literal["quick", "normal", "full_topic", "difficult", "due_today", "unit_mixed"]
    title: str
    description: str
    availableCount: int
    sessionSize: int
    enabled: bool


class FlashcardStudyOptionsResponse(BaseModel):
    deckRef: str
    options: list[FlashcardStudyOption]
    summary: dict[str, int] = Field(default_factory=dict)
