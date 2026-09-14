import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator

class DeterministicMediaCreate(BaseModel):
    kind: Literal["circuit_svg", "forces_svg", "geometry_svg", "plot_svg"]
    subjectId: str
    sourceChunkId: uuid.UUID
    title: str = Field(min_length=2, max_length=180)
    altText: str = Field(min_length=10, max_length=1000)
    parameters: dict = Field(default_factory=dict)

class IllustrationCreate(BaseModel):
    subjectId: str
    sourceChunkId: uuid.UUID
    title: str = Field(min_length=2, max_length=180)
    altText: str = Field(min_length=10, max_length=1000)
    prompt: str = Field(min_length=20, max_length=4000)

class MediaReview(BaseModel):
    decision: Literal["published", "rejected"]
    notes: str = Field(min_length=3, max_length=2000)

class MediaResponse(BaseModel):
    id: uuid.UUID; subjectId: str; unitId: uuid.UUID; sourceChunkId: uuid.UUID
    kind: str; title: str; altText: str; prompt: str; promptVersion: str
    parameters: dict; sourceManifest: list[dict]; provider: str; model: str
    responseId: str | None; contentType: str; status: str; reviewNotes: str
    createdAt: datetime; reviewedAt: datetime | None; contentUrl: str

class MediaListResponse(BaseModel):
    media: list[MediaResponse]

class MediaSourceResponse(BaseModel):
    id: uuid.UUID; subjectId: str; unitCode: str; unitTitle: str; documentTitle: str; page: int; excerpt: str
