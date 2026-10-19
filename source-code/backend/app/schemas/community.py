"""Minimal community contracts; never serialize private Student/account records."""
import unicodedata
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator
from app.schemas.student_avatar import StudentAvatarConfig


class CommunitySettingsDraft(BaseModel):
    model_config = ConfigDict(extra='forbid')
    publicName: str = Field(max_length=64)
    enabled: StrictBool
    visibleSubjectIds: list[str] = Field(default_factory=list, max_length=50)

    @field_validator('publicName')
    @classmethod
    def public_name(cls, value):
        value = ' '.join(unicodedata.normalize('NFKC', value).split())
        if not 3 <= len(value) <= 32 or not all(c.isalpha() or c.isdigit() or c in " -_" for c in value):
            raise ValueError('Use 3–32 letters, numbers, spaces, hyphens or underscores.')
        compact = ''.join(c for c in value.casefold() if c.isalnum())
        if any(word in compact for word in ('admin', 'akuru', 'moderator', 'support', 'fuck', 'shit', 'bitch', 'nigger', 'cunt')):
            raise ValueError('Please choose a different public name.')
        return value


class CommunityChoice(BaseModel):
    id: str
    name: str


class CommunitySettings(BaseModel):
    publicName: str
    enabled: bool
    visibleSubjectIds: list[str]
    nameChangeRequired: bool
    courses: list[CommunityChoice]
    subjects: list[CommunityChoice]


class CommunityMember(BaseModel):
    ref: str
    publicName: str
    avatar: StudentAvatarConfig | None
    subjects: list[CommunityChoice]
    following: bool
    followsYou: bool


class CommunityPage(BaseModel):
    members: list[CommunityMember]
    hasMore: bool
    page: int


class CommunityNotice(BaseModel):
    ref: str
    type: Literal['follow.v1']
    actor: CommunityMember
    createdAt: datetime
    read: bool


class CommunityFeed(BaseModel):
    notifications: list[CommunityNotice]
    unreadCount: int
    hasMore: bool
    page: int


class NoticeRead(BaseModel):
    model_config = ConfigDict(extra='forbid')
    read: StrictBool


class ReportDraft(BaseModel):
    model_config = ConfigDict(extra='forbid')
    reason: Literal['inappropriate_name', 'impersonation', 'other_concern']


class ReportDecision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['dismissed', 'name_change_required']


class CommunityReportView(BaseModel):
    ref: str
    publicName: str
    reason: str
    status: str
    createdAt: datetime


class CommunityReports(BaseModel):
    reports: list[CommunityReportView]
    hasMore: bool
    page: int


class CommunityResult(BaseModel):
    ok: bool = True


class CommunitySubjectChoices(BaseModel):
    subjects: list[CommunityChoice]
