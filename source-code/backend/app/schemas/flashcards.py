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
    mode: Literal["review", "difficult"] = "review"
    difficulty: Literal["easy", "difficult", "mixed"] | None = None
    requestedCount: Literal[20, 30] = 20

    @model_validator(mode="after")
    def valid_selection(self):
        if self.mode == "review" and self.difficulty is None:
            raise ValueError("Review Flashcards requires Easy, Difficult or Mixed difficulty.")
        if self.mode == "difficult" and self.difficulty is not None:
            raise ValueError("Difficult Flashcards determines eligibility from Student mastery.")
        return self


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
    explanation: str | None = None
    status: str
    warnings: list[str]
    source: dict
    conceptKey: str = ""
    category: str = "essential_knowledge"
    variationType: str = "recall"
    difficulty: str = "easy"
    selectedRating: str | None = None
    attempted: bool = False


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
    masteryVersion: str
    selectionVersion: str
    message: str
    mode: Literal["review", "difficult"] = "review"
    difficulty: Literal["easy", "difficult", "mixed"] | None = None
    selectionReasons: list[str] = Field(default_factory=list)
    viewedOrdinal: int
    firstUnattemptedOrdinal: int
    canGoPrevious: bool = False
    canGoNext: bool = False
    hasUncommittedResults: bool = False


class FlashcardStudyOption(BaseModel):
    mode: Literal["review", "difficult"]
    title: str
    description: str
    availableCount: int
    sessionSize: int
    enabled: bool
    supportedCounts: list[int] = Field(default_factory=list)
    difficulties: list[str] = Field(default_factory=list)


class FlashcardStudyOptionsResponse(BaseModel):
    deckRef: str
    options: list[FlashcardStudyOption]
    summary: dict[str, int] = Field(default_factory=dict)


class FlashcardMasteryCategory(BaseModel):
    category: str
    total: int
    toEvaluate: int
    needsReview: int
    good: int
    mastered: int
    coveragePercent: float
    masteryPercent: float


class FlashcardMasterySession(BaseModel):
    sessionRef: str
    mode: Literal["review", "difficult"]
    difficulty: Literal["easy", "difficult", "mixed"] | None = None
    cardCount: int
    completedAt: str


class FlashcardMasteryResponse(BaseModel):
    deckRef: str
    totalCards: int
    toEvaluate: int
    needsReview: int
    good: int
    mastered: int
    coveragePercent: float
    masteryPercent: float
    categories: list[FlashcardMasteryCategory]
    completedSessions: int
    recentSessions: list[FlashcardMasterySession] = Field(default_factory=list)
    recommendedMode: Literal["review", "difficult"]
    recommendedDifficulty: Literal["easy", "difficult", "mixed"] | None = None
    recommendedCount: Literal[20, 30] = 20
    masteryVersion: str
    recalculatedAt: str | None = None


class FlashcardDiscardResponse(BaseModel):
    sessionRef: str
    status: Literal["discarded"]
    message: str
