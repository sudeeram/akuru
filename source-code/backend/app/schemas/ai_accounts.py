import re

from pydantic import BaseModel, Field, field_validator


ALIAS_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{1,39}$")


class AIAccountWriteRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    credentialAlias: str = Field(min_length=2, max_length=40)
    priority: int = Field(ge=0, le=100)
    model: str = Field(min_length=2, max_length=120)
    enabled: bool = True

    @field_validator("name", "model")
    @classmethod
    def clean_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value is required.")
        return value

    @field_validator("credentialAlias")
    @classmethod
    def clean_alias(cls, value: str) -> str:
        value = value.strip().upper()
        if not ALIAS_PATTERN.fullmatch(value):
            raise ValueError("Use 2–40 uppercase letters, numbers or underscores, beginning with a letter.")
        return value


class AIAccountResponse(BaseModel):
    name: str
    credentialAlias: str
    priority: int
    model: str
    enabled: bool
    credentialConfigured: bool
    healthStatus: str
    cooldownUntil: str | None = None
    lastErrorCode: str | None = None
    lastSuccessAt: str | None = None
    lastFailureAt: str | None = None
