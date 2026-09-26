import re
import uuid
from typing import Literal

from pydantic import BaseModel, Field, model_validator


USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,39}$")


class CreateAccountRequest(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=12, max_length=200)
    role: Literal["parent", "student"]
    parentId: uuid.UUID | None = None
    level: Literal["iGCSE"] | None = None
    grade: Literal["Grade 10", "Grade 11"] | None = None
    term: Literal["Term1", "Term2", "Term3"] | None = None
    progression: list[str] = Field(default_factory=list, max_length=6)
    subjects: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def validate_account(self):
        self.username = self.username.strip().lower()
        self.name = self.name.strip()
        if not USERNAME_PATTERN.fullmatch(self.username):
            raise ValueError("Username must use 3–40 lowercase letters, numbers, underscores or hyphens.")
        if not self.name:
            raise ValueError("Name is required.")
        if self.role == "student" and not all(
            (self.parentId, self.level, self.grade, self.term, self.progression, self.subjects)
        ):
            raise ValueError("Students require a parent, iGCSE progression, and at least one subject.")
        return self


class UpdateStudentRequest(BaseModel):
    id: uuid.UUID
    name: str = Field(min_length=1, max_length=160)
    parentId: uuid.UUID
    level: Literal["iGCSE"]
    grade: Literal["Grade 10", "Grade 11"]
    term: Literal["Term1", "Term2", "Term3"]
    progression: list[str] = Field(min_length=1, max_length=6)
    subjects: list[str] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def clean_name(self):
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("Name is required.")
        return self


class AccountResponse(BaseModel):
    id: str
    publicRef: str
    username: str
    name: str
    role: Literal["parent", "student"]
    lastLoginAt: str | None = None

class AdminPasswordResetRequest(BaseModel):
    requestKey: str = Field(min_length=8, max_length=100)

class AdminPasswordResetResponse(BaseModel):
    accountRef: str
    username: str
    temporaryPassword: str
    sessionsRevoked: int
    mustChangePassword: Literal[True] = True


class AccountSecurityEventResponse(BaseModel):
    action: str
    actorName: str
    targetRef: str
    occurredAt: str
    details: dict
