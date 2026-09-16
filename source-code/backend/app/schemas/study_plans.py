import uuid
from datetime import datetime
from pydantic import BaseModel

class PlanGenerateRequest(BaseModel):
    studentId: uuid.UUID | None = None

class PlanItemResponse(BaseModel):
    id: uuid.UUID; subject: str; unitId: uuid.UUID | None = None; unitCode: str | None = None; topic: str
    topicRef: str | None = None; topicCode: str | None = None; topicTitle: str | None = None
    groupLabel: str | None = None; groupCode: str | None = None; groupTitle: str | None = None
    activityType: str; minutes: int; reason: str; source: str; sourceUrl: str
    successCondition: str; scheduledFor: datetime; status: str

class StudyPlanResponse(BaseModel):
    id: uuid.UUID; studentId: uuid.UUID; version: int; updatedAt: datetime
    generationReason: str; items: list[PlanItemResponse]

class PlanHistoryResponse(BaseModel):
    plans: list[StudyPlanResponse]
