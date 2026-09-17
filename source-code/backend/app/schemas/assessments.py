import uuid
from datetime import datetime
from enum import StrEnum
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class AssessmentMode(StrEnum):
    PRACTICE = "practice"
    OFFICIAL_PAPER = "official_paper"
    MOCK = "mock"

class BlueprintCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    subjectId: str
    grade: Literal[10, 11]
    term: Literal[1, 2, 3]
    mode: Literal["mock"] = "mock"
    targetMarks: int = Field(gt=0, le=300)
    durationMinutes: int = Field(gt=0, le=300)
    questionCount: int = Field(gt=0, le=100)
    skills: list[str] = Field(default_factory=list, max_length=30)
    difficultyProfile: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def valid_difficulty(self):
        if any(key not in {"foundation", "standard", "stretch", "mixed"} or value < 0 for key, value in self.difficultyProfile.items()):
            raise ValueError("Difficulty profile may contain non-negative foundation, standard, stretch or mixed counts only.")
        if self.difficultyProfile and sum(self.difficultyProfile.values()) != self.questionCount:
            raise ValueError("Difficulty profile counts must equal questionCount.")
        return self

class BlueprintResponse(BlueprintCreate):
    id: uuid.UUID
    status: str

class AssessmentStart(BaseModel):
    mode: AssessmentMode
    subjectId: str
    blueprintId: uuid.UUID | None = None
    paperId: uuid.UUID | None = None

class AnswerSave(BaseModel):
    questionId: uuid.UUID
    answer: str = Field(default="", max_length=100_000)
    fileId: str | None = Field(default=None, max_length=120)
    idempotencyKey: str = Field(min_length=8, max_length=100)

class SubmissionRequest(BaseModel):
    idempotencyKey: str = Field(min_length=8, max_length=100)

class AssessmentEvaluateRequest(BaseModel):
    idempotencyKey: str = Field(min_length=8, max_length=100)

class MarkingDecision(BaseModel):
    pointId: str = Field(min_length=1, max_length=80)
    criterion: str = Field(min_length=1, max_length=2000)
    awarded: bool
    marksAwarded: int = Field(ge=0, le=100)
    maxMarks: int = Field(gt=0, le=100)
    studentEvidence: str = Field(min_length=1, max_length=2000)
    rationale: str = Field(min_length=1, max_length=2000)
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def valid_marks(self):
        if self.marksAwarded > self.maxMarks or (not self.awarded and self.marksAwarded):
            raise ValueError("A marking point cannot award more than its maximum.")
        return self

class AssessmentPassOne(BaseModel):
    decisions: list[MarkingDecision]
    overallConfidence: float = Field(ge=0, le=1)
    reviewReasons: list[str] = Field(default_factory=list, max_length=20)

class AssessmentPassTwo(BaseModel):
    decisions: list[MarkingDecision]
    strengths: list[str] = Field(default_factory=list, max_length=30)
    smallMistakes: list[str] = Field(default_factory=list, max_length=30)
    conceptualMistakes: list[str] = Field(default_factory=list, max_length=30)
    improvedAnswer: str = Field(min_length=1, max_length=20_000)
    teachingExplanation: str = Field(min_length=1, max_length=30_000)
    topicEvidence: list[dict] = Field(default_factory=list, max_length=30)
    recommendations: list[str] = Field(default_factory=list, max_length=30)
    confidence: float = Field(ge=0, le=1)
    reviewReasons: list[str] = Field(default_factory=list, max_length=20)

class AssessmentResultResponse(BaseModel):
    id: uuid.UUID
    version: int
    status: str
    awardedMarks: int
    maxMarks: int
    confidence: float
    markingDecisions: list[MarkingDecision]
    strengths: list[str]
    smallMistakes: list[str]
    conceptualMistakes: list[str]
    improvedAnswer: str
    teachingExplanation: str
    topicEvidence: list[dict]
    recommendations: list[str]
    reviewReasons: list[str]
    subjectEngine: str
    subjectEngineVersion: str
    deterministicChecks: dict
    createdAt: datetime

class WorkingFileResponse(BaseModel):
    id: uuid.UUID
    name: str
    contentType: str
    ocrText: str
    ocrConfidence: float
    needsReview: bool

class AssessmentQuestionResponse(BaseModel):
    id: uuid.UUID
    number: str
    prompt: str
    sharedStem: str
    marks: int
    equations: list
    assetIds: list
    sourceLocations: list
    topicRefs: list[str] = Field(default_factory=list)
    skills: list
    difficulty: str
    answer: str = ""
    fileId: str | None = None
    saveRevision: int = 0
    rubric: dict | None = None
    result: AssessmentResultResponse | None = None

class AssessmentResponse(BaseModel):
    id: uuid.UUID
    studentId: uuid.UUID
    subjectId: str
    mode: str
    status: str
    title: str
    targetMarks: int
    durationMinutes: int
    startedAt: datetime
    endsAt: datetime
    submittedAt: datetime | None
    skills: list
    difficultyProfile: dict
    feedbackVisible: bool
    questions: list[AssessmentQuestionResponse]

class AssessmentListResponse(BaseModel):
    assessments: list[AssessmentResponse]

class AssessmentAuditResponse(BaseModel):
    resultId: uuid.UUID; assessmentId: uuid.UUID; questionId: uuid.UUID; studentId: uuid.UUID
    studentName: str; subjectId: str; assessmentTitle: str; questionNumber: str; questionPrompt: str
    version: int; status: str; awardedMarks: int; maxMarks: int; confidence: float
    provider: str; model: str; promptName: str; promptVersion: str
    subjectEngine: str; subjectEngineVersion: str; reviewReasons: list[str]
    markingDecisions: list[dict]; strengths: list[str]; smallMistakes: list[str]; conceptualMistakes: list[str]
    improvedAnswer: str; teachingExplanation: str; deterministicChecks: dict; sourceManifest: list[dict]
    createdAt: datetime
    answer: str
    workingUrl: str | None

class AssessmentAuditListResponse(BaseModel):
    results: list[AssessmentAuditResponse]

class AssessmentReviewRequest(BaseModel):
    idempotencyKey: str = Field(min_length=8, max_length=100)
    markingDecisions: list[MarkingDecision] = Field(min_length=1, max_length=100)
    feedback: str = Field(min_length=1, max_length=30000)
    improvedAnswer: str = Field(min_length=1, max_length=20000)
    strengths: list[str] = Field(default_factory=list, max_length=30)
    smallMistakes: list[str] = Field(default_factory=list, max_length=30)
    conceptualMistakes: list[str] = Field(default_factory=list, max_length=30)
    reason: str = Field(min_length=1, max_length=2000)
