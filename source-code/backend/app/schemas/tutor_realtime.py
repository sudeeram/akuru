from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


LanguageMode = Literal[
    "auto",
    "french_conversation",
    "french_vocabulary",
    "french_pronunciation",
]


class RealtimeCredentialRequest(BaseModel):
    requestKey: str = Field(min_length=8, max_length=100)
    languageMode: LanguageMode = "auto"
    failedConnectionRef: str | None = Field(default=None, min_length=8, max_length=56)


class RealtimeCredentialResponse(BaseModel):
    connectionRef: str
    clientSecret: str
    expiresAt: datetime
    model: str
    voiceReady: bool = True
    reconnect: bool


class RealtimeConnectionStateRequest(BaseModel):
    state: Literal["connected", "ended", "failed", "cancelled"]
    failureCode: str | None = Field(default=None, max_length=80)


class RealtimeConnectionStateResponse(BaseModel):
    connectionRef: str
    state: Literal["connecting", "connected", "ended", "failed", "cancelled"]
    billedSeconds: int | None = None


class RealtimeTranscriptTurnRequest(BaseModel):
    role: Literal["student", "assistant"]
    content: str = Field(min_length=1, max_length=8000)
    requestKey: str = Field(min_length=8, max_length=100)


class RealtimeTranscriptTurnResponse(BaseModel):
    turnRef: str
    role: Literal["student", "assistant"]
    content: str
    createdAt: datetime
