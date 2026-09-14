from typing import Literal

from pydantic import BaseModel, Field, field_validator


Presentation = Literal["masculine", "feminine", "neutral"]
Level = Literal["low", "medium", "high"]
Tone = Literal["calm", "encouraging", "direct", "playful"]
Character = Literal["childlike", "balanced", "authoritative"]
Depth = Literal["concise", "standard", "detailed"]
TeachingStyle = Literal["guided", "socratic", "example_led", "exam_focused"]


class TutorAvatarResponse(BaseModel):
    code: str
    name: str
    description: str
    imagePath: str
    presentation: Presentation
    enabled: bool | None = None
    sortOrder: int | None = None


class TutorVoiceResponse(BaseModel):
    code: str
    name: str
    description: str
    presentation: Presentation
    enabled: bool | None = None
    sortOrder: int | None = None


class TutorOptionsResponse(BaseModel):
    presentations: list[str]
    tones: list[str]
    levels: list[str]
    communicationCharacters: list[str]
    explanationDepths: list[str]
    teachingStyles: list[str]
    avatars: list[TutorAvatarResponse]
    voices: list[TutorVoiceResponse]


class TutorProfileInput(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    presentation: Presentation
    avatarCode: str = Field(min_length=2, max_length=40)
    voiceCode: str = Field(min_length=2, max_length=40)
    tone: Tone = "encouraging"
    friendliness: Level = "medium"
    enthusiasm: Level = "medium"
    speed: Level = "medium"
    communicationCharacter: Character = "balanced"
    explanationDepth: Depth = "standard"
    teachingStyle: TeachingStyle = "guided"

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Enter a tutor name with at least 2 characters.")
        if any(ord(character) < 32 for character in cleaned):
            raise ValueError("Tutor name contains unsupported characters.")
        lowered = cleaned.lower()
        if "<" in cleaned or ">" in cleaned or "http://" in lowered or "https://" in lowered:
            raise ValueError("Choose a simple, child-safe tutor name.")
        return cleaned


class TutorProfileResponse(TutorProfileInput):
    profileRef: str
    version: int
    active: bool


class TutorProfileListResponse(BaseModel):
    profiles: list[TutorProfileResponse]


class TutorPresetUpdate(BaseModel):
    enabled: bool
    sortOrder: int = Field(ge=0, le=1000)


class TutorAdminPresetsResponse(BaseModel):
    avatars: list[TutorAvatarResponse]
    voices: list[TutorVoiceResponse]
