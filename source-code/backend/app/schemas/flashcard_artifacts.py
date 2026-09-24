from typing import Literal
from pydantic import BaseModel, Field, model_validator

Category = Literal["essential_knowledge", "explanation_comparison", "application_misconception", "calculation_interpretation_diagram"]
Variation = Literal["recall", "explanation", "comparison", "application", "misconception", "calculation", "interpretation", "diagram"]
Difficulty = Literal["foundation", "core", "stretch"]


class CuratedFlashcard(BaseModel):
    key: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,119}$")
    conceptKey: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,119}$")
    category: Category
    variationType: Variation
    difficulty: Difficulty = "core"
    question: str = Field(min_length=5, max_length=500)
    answer: str = Field(min_length=2, max_length=3000)
    sourceChunkRefs: list[str] = Field(min_length=1, max_length=5)
    visualAssetRef: str | None = Field(default=None, max_length=56)
    visualAltText: str | None = Field(default=None, max_length=500)
    reviewer: str = Field(min_length=2, max_length=120)
    reviewNote: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def diagram_has_accessible_visual(self):
        if self.variationType == "diagram" and (not self.visualAssetRef or not self.visualAltText):
            raise ValueError("Diagram cards require an approved visual asset and alternative text.")
        return self


class CuratedFlashcardDeck(BaseModel):
    key: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,119}$")
    title: str = Field(min_length=3, max_length=240)
    topicRef: str = Field(min_length=8, max_length=80)
    contentVersionRef: str = Field(min_length=8, max_length=80)
    requiredConceptKeys: list[str] = Field(min_length=1)
    cards: list[CuratedFlashcard] = Field(min_length=3, max_length=100)


class FlashcardReleaseArtifact(BaseModel):
    schemaVersion: Literal["akuru.flashcards.v1"]
    releaseId: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{7,79}$")
    courseId: str = Field(min_length=2, max_length=32)
    subjectId: str = Field(min_length=2, max_length=32)
    textbookRef: str = Field(min_length=8, max_length=80)
    groupRef: str = Field(min_length=8, max_length=80)
    createdAt: str
    editor: str = Field(min_length=2, max_length=120)
    generator: str = Field(default="human_curated", max_length=120)
    generatorVersion: str = Field(default="1", max_length=40)
    sourceContentChecksums: dict[str, str]
    decks: list[CuratedFlashcardDeck] = Field(min_length=1)
    artifactChecksum: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def unique_keys(self):
        deck_keys = [deck.key for deck in self.decks]
        if len(deck_keys) != len(set(deck_keys)):
            raise ValueError("Deck keys must be unique.")
        card_keys = [card.key for deck in self.decks for card in deck.cards]
        if len(card_keys) != len(set(card_keys)):
            raise ValueError("Card keys must be unique across the release.")
        return self
