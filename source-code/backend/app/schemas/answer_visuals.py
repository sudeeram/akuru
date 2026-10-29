"""Private model-answer associations, never question illustrations."""
import uuid
from typing import Literal
from pydantic import BaseModel, Field

class AnswerVisual(BaseModel):
    assetId: uuid.UUID
    partLabel: str = Field(default="", max_length=40)
    pointCodes: list[str] = Field(default_factory=list, max_length=200)
    caption: str = Field(default="", max_length=2000)
    altText: str = Field(min_length=10, max_length=2000)
    status: Literal["proposed", "approved", "rejected"] = "proposed"
