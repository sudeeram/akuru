from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class UserResponse(BaseModel):
    id: str
    username: str
    name: str
    role: Literal["admin", "parent", "student"]
    mustChangePassword: bool


class LoginResponse(BaseModel):
    user: UserResponse
    csrfToken: str


class ChangePasswordRequest(BaseModel):
    newPassword: str = Field(min_length=12, max_length=200)

class NormalPasswordChangeRequest(BaseModel):
    currentPassword: str = Field(min_length=1, max_length=200)
    newPassword: str = Field(min_length=12, max_length=200)
