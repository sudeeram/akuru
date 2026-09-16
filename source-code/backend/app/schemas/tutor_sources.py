from typing import Literal

from pydantic import BaseModel, Field


class TutorSourceSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    textbookEdition: str | None = Field(default=None, min_length=1, max_length=80)
    limit: int = Field(default=5, ge=1, le=10)


class TutorCitation(BaseModel):
    citationRef: str
    documentVersion: int
    textbookTitle: str
    textbookEdition: str
    unitId: str | None = None
    unitCode: str | None = None
    unitTitle: str | None = None
    topicRef: str | None = None
    topicCode: str | None = None
    topicTitle: str | None = None
    groupLabel: str | None = None
    groupCode: str | None = None
    groupTitle: str | None = None
    contentKind: str
    passage: str
    pdfPageIndex: int
    pdfPageNumber: int
    printedPageLabel: str | None = None
    pageReference: str
    boundingBox: dict
    confidence: float
    assetRef: str
    sourceUrl: str
    assetUrl: str


class TutorSourceSearchResponse(BaseModel):
    status: Literal["exact", "evidence_insufficient"]
    message: str
    query: str
    citations: list[TutorCitation] = Field(default_factory=list)


class TutorCitationContextResponse(BaseModel):
    citation: TutorCitation
    nearbyPassages: list[TutorCitation]
    groundingInstruction: str
