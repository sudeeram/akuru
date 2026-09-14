from enum import StrEnum

from pydantic import BaseModel


class TutoringPurpose(StrEnum):
    EXPLANATION = "explanation"
    FEEDBACK = "feedback"
    STUDY_PLAN = "study_plan"


class TutorCapabilitiesResponse(BaseModel):
    textEnabled: bool
    voiceEnabled: bool
    toolsEnabled: bool
    blockedReason: str | None = None
