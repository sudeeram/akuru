"""Bounded preparation contract. Extra source metadata is preserved, never executed."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class SourceRecord(BaseModel):
    model_config = ConfigDict(extra="allow")


class PreparedPage(SourceRecord):
    id: str = Field(min_length=1, max_length=80)
    printedPage: str = Field(min_length=1, max_length=24)
    sourcePath: str = Field(min_length=1, max_length=240)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    width: int = Field(gt=0, le=10000)
    height: int = Field(gt=0, le=10000)


class PreparedBlock(SourceRecord):
    id: str = Field(min_length=1, max_length=80)
    page: int = Field(gt=0)
    kind: Literal["heading", "paragraph", "table", "equation", "list", "sidebar", "example", "definition", "procedure", "safety_note"]
    title: str = Field(default="", max_length=1000)
    text: str = Field(default="", max_length=30000)
    latex: str | None = Field(default=None, max_length=10000)
    columns: list[str] = Field(default_factory=list, max_length=40)
    rows: list[list[str | None]] = Field(default_factory=list, max_length=500)
    figureRefs: list[str] = Field(default_factory=list, max_length=100)
    items: list[str] = Field(default_factory=list, max_length=100)


class PreparedFigure(SourceRecord):
    id: str = Field(min_length=1, max_length=80)
    page: int = Field(gt=0)
    pageId: str = Field(min_length=1, max_length=80)
    path: str = Field(min_length=1, max_length=240)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    caption: str = Field(min_length=1, max_length=900)
    altText: str = Field(min_length=1, max_length=2000)
    bboxPixels: list[int] = Field(min_length=4, max_length=4)


class PreparedIssue(SourceRecord):
    id: str = Field(min_length=1, max_length=80)
    page: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=1000)
    blocks: list[str] = Field(min_length=1, max_length=100)
    reason: str = Field(default="", max_length=5000)
    action: str = Field(default="", max_length=5000)


class PreparedExercisePart(SourceRecord):
    label: str = Field(max_length=80)
    prompt: str = Field(min_length=1, max_length=10000)
    figureRefs: list[str] = Field(default_factory=list, max_length=100)


class PreparedExercise(SourceRecord):
    id: str = Field(min_length=1, max_length=80)
    page: int = Field(gt=0)
    stem: str = Field(max_length=10000)
    parts: list[PreparedExercisePart] = Field(min_length=1, max_length=100)
    wordBank: list[str] = Field(default_factory=list, max_length=100)


class PreparedPackage(SourceRecord):
    format: Literal["akuru-textbook-preparation-v1"]
    identity: dict
    provenance: dict
    guideline: dict
    pages: list[PreparedPage] = Field(min_length=1, max_length=100)
    blocks: list[PreparedBlock] = Field(min_length=1, max_length=2000)
    figures: list[PreparedFigure] = Field(default_factory=list, max_length=300)
    objectives: list[dict] = Field(default_factory=list, max_length=100)
    exercises: list[PreparedExercise] = Field(default_factory=list, max_length=300)
    reviewIssues: list[PreparedIssue] = Field(default_factory=list, max_length=100)


class PreparedReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contentHash: str = Field(pattern=r"^[a-f0-9]{64}$")
    confirmWholeDocument: bool
    # Notes become explicit editorial annotations on the affected blocks; corrections
    # to source wording can be made in the normal block editor before confirmation.
    decisions: dict[str, str] = Field(default_factory=dict, max_length=100)
