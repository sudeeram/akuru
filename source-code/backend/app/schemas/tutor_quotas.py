from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class QuotaAmount(BaseModel):
    allowance: int
    used: int
    remaining: int


class StudentQuotaResponse(BaseModel):
    studentRef: str
    studentName: str
    enabled: bool
    state: Literal["available", "warning", "exhausted", "disabled", "renewed"]
    periodDays: int
    periodStartsAt: datetime
    renewsAt: datetime
    requests: QuotaAmount
    textTokens: QuotaAmount
    voiceMinutes: QuotaAmount
    fallbackMessage: str


class AdminQuotaListResponse(BaseModel):
    quotas: list[StudentQuotaResponse]


class AdminQuotaUpdate(BaseModel):
    periodDays: int = Field(ge=1, le=366)
    requestAllowance: int = Field(ge=0, le=1000000)
    textTokenAllowance: int = Field(ge=0, le=1000000000)
    voiceMinuteAllowance: int = Field(ge=0, le=1000000)
    enabled: bool = True
    reason: str = Field(min_length=3, max_length=300)


class QuotaAuditItem(BaseModel):
    action: str
    reason: str
    changes: dict
    createdAt: datetime


class QuotaAuditResponse(BaseModel):
    studentRef: str
    events: list[QuotaAuditItem]
