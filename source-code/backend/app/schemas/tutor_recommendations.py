from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.curriculum_plans import PlanTopicResponse


class NextTopicRequest(BaseModel):
    subjectId: str = Field(min_length=2, max_length=32)
    requestKey: str = Field(min_length=8, max_length=100)


class RecommendationActivity(BaseModel):
    type: Literal["review", "targeted_practice", "spaced_retry", "unit_check"]
    title: str
    instruction: str
    successCondition: str


class RankingFactor(BaseModel):
    factor: str
    points: float
    explanation: str
    evidenceRefs: list[str] = Field(default_factory=list)


class RankedTopic(BaseModel):
    topic: PlanTopicResponse
    score: float
    factors: list[RankingFactor]
    evidenceRefs: list[str]


class NextTopicRecommendation(BaseModel):
    topic: PlanTopicResponse
    reason: str
    evidenceRefs: list[str]
    activity: RecommendationActivity
    requiresStudentAction: bool = True
    moveAction: dict


class TutorRecommendationBrief(BaseModel):
    instruction: str
    fixedTopicRef: str
    fixedReason: str
    evidenceRefs: list[str]


class NextTopicResponse(BaseModel):
    status: Literal["ready", "no_evidence", "no_eligible_topics"]
    message: str
    algorithmVersion: str
    contextOperationRef: str | None = None
    contextVersion: str | None = None
    recommendation: NextTopicRecommendation | None = None
    ranking: list[RankedTopic] = Field(default_factory=list)
    tutorBrief: TutorRecommendationBrief | None = None
