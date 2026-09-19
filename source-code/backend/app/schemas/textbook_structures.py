from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TextbookCreateRequest(BaseModel):
    courseId: Literal["igcse"] = "igcse"
    subjectId: str = Field(min_length=1, max_length=32)
    title: str = Field(min_length=1, max_length=240)
    edition: str = Field(min_length=1, max_length=80)
    publisher: str = Field(default="", max_length=160)
    groupLabel: Literal["unit", "module"]

    @model_validator(mode="after")
    def trim_values(self):
        self.subjectId = self.subjectId.strip().lower()
        self.title = self.title.strip()
        self.edition = self.edition.strip()
        self.publisher = self.publisher.strip()
        if not self.subjectId or not self.title or not self.edition:
            raise ValueError("Subject, title and edition are required.")
        return self


class TextbookUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    edition: str = Field(min_length=1, max_length=80)
    publisher: str = Field(default="", max_length=160)
    groupLabel: Literal["unit", "module"]

    @model_validator(mode="after")
    def trim_values(self):
        self.title = self.title.strip()
        self.edition = self.edition.strip()
        self.publisher = self.publisher.strip()
        if not self.title or not self.edition:
            raise ValueError("Title and edition are required.")
        return self


class GroupSaveRequest(BaseModel):
    code: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=240)
    summary: str = Field(default="", max_length=5000)
    sequence: int = Field(ge=1, le=500)

    @model_validator(mode="after")
    def trim_values(self):
        self.code = self.code.strip()
        self.title = self.title.strip()
        self.summary = self.summary.strip()
        if not self.code or not self.title:
            raise ValueError("Group code and title are required.")
        return self


class TopicSaveRequest(BaseModel):
    code: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=240)
    sequence: int = Field(ge=1, le=2000)
    syllabusRef: str = Field(default="", max_length=120)
    description: str = Field(default="", max_length=5000)

    @model_validator(mode="after")
    def trim_values(self):
        self.code = self.code.strip()
        self.title = self.title.strip()
        self.syllabusRef = self.syllabusRef.strip()
        self.description = self.description.strip()
        if not self.code or not self.title:
            raise ValueError("Topic code and title are required.")
        return self


class ReorderRequest(BaseModel):
    refs: list[str] = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def unique_refs(self):
        if len(self.refs) != len(set(self.refs)):
            raise ValueError("Every item must appear exactly once.")
        return self


class PublishStructureRequest(BaseModel):
    confirmCourse: bool
    confirmSubject: bool
    confirmEdition: bool
    confirmStructure: bool


class PublishTopicContentRequest(BaseModel):
    confirmSources: bool
    confirmExtraction: bool
    confirmTopic: bool


class TopicDocumentRoleUpdateRequest(BaseModel):
    role: Literal["primary", "supporting", "reference", "visual_reference"]


class TopicDocumentSourceResponse(BaseModel):
    documentId: str
    documentVersionId: str
    filename: str
    role: Literal["primary", "supporting", "reference", "visual_reference"]
    sequence: int
    reviewStatus: str
    documentStatus: str
    libraryReviewState: str
    unresolvedPageCount: int
    unresolvedBlockCount: int
    includedInRetrieval: bool
    usedByPublishedVersion: bool
    publishableBlockCount: int
    visualAssetCount: int
    selectedVisualCount: int = 0
    approvedVisualCount: int = 0
    pendingVisualCount: int = 0
    duplicateOf: list[str] = Field(default_factory=list)


class TopicVisualAssetUpdateRequest(BaseModel):
    status: Literal["selected", "approved", "rejected"]
    caption: str = Field(default="", max_length=1000)
    altText: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def validate_review(self):
        self.caption = " ".join(self.caption.split())
        self.altText = " ".join(self.altText.split())
        if self.status == "approved" and not self.altText:
            raise ValueError("Approved visual assets require a text alternative.")
        return self


class TopicVisualAssetResponse(BaseModel):
    assetRef: str
    documentId: str
    documentVersionId: str
    documentAssetId: str
    filename: str
    sourceRole: str
    kind: str
    page: int
    printedPage: str | None = None
    boundingBox: dict
    extractedCaption: str
    status: Literal["unselected", "selected", "approved", "rejected"]
    caption: str
    altText: str
    contentUrl: str


class TopicReviewChecklistResponse(BaseModel):
    topicRef: str
    topicTitle: str
    remainingPages: int
    remainingBlocks: int
    notationBlocks: int
    tableBlocks: int
    visualBlocks: int
    pendingVisualAssets: int
    checks: list[dict]


class TopicQualityCheck(BaseModel):
    code: str
    threshold: float
    value: float
    passed: bool


class TopicDocumentQualityReport(BaseModel):
    documentId: str
    filename: str
    role: str
    reviewStatus: str
    pageCount: int
    equationCount: int
    diagramCount: int
    passed: bool
    checks: list[TopicQualityCheck]


class TopicQualityReport(BaseModel):
    topicRef: str
    topicCode: str
    topicTitle: str
    thresholds: dict[str, float]
    passed: bool
    documents: list[TopicDocumentQualityReport]
    resolution: str


class TopicReadinessResponse(BaseModel):
    state: str
    ready: bool
    contentVersion: int
    supersededVersionCount: int
    hasDraftChanges: bool
    documentCount: int
    primaryDocumentCount: int
    processingCount: int
    needsReviewCount: int
    failedCount: int
    unresolvedPageCount: int
    unresolvedBlockCount: int
    averageConfidence: float
    checks: list[dict]


class TopicLaunchReadinessResponse(BaseModel):
    topicRef: str
    topicTitle: str
    overallStatus: Literal["ready", "blocked"]
    checks: list[dict]


class TopicRetrievalPreflightRequest(BaseModel):
    queries: list[str] = Field(default_factory=lambda: [
        "three states of matter", "particle arrangement", "melting", "diffusion", "sublimation",
    ], min_length=1, max_length=20)

    @model_validator(mode="after")
    def clean_queries(self):
        self.queries = [" ".join(query.split()) for query in self.queries if query.strip()]
        if not self.queries:
            raise ValueError("At least one retrieval check is required.")
        return self


class TopicRetrievalPreflightResponse(BaseModel):
    preflightRef: str
    topicRef: str
    contentVersion: int
    passed: bool
    queries: list[str]
    results: list[dict]
    createdAt: str


class TopicResponse(BaseModel):
    topicRef: str
    code: str
    title: str
    sequence: int
    syllabusRef: str
    description: str
    status: str
    documentCount: int
    removable: bool
    content: TopicReadinessResponse


class GroupResponse(BaseModel):
    groupRef: str
    code: str
    title: str
    summary: str
    sequence: int
    status: str
    topics: list[TopicResponse]
    removable: bool
    totalTopicCount: int
    reviewedTopicCount: int
    publishedTopicCount: int
    studentEligibleTopicCount: int


class TextbookResponse(BaseModel):
    textbookRef: str
    courseId: str
    subjectId: str
    title: str
    edition: str
    publisher: str
    groupLabel: Literal["unit", "module"]
    groupDisplayLabel: Literal["Unit", "Module"]
    status: str
    structureVersion: int
    groups: list[GroupResponse]


class TextbookListResponse(BaseModel):
    textbooks: list[TextbookResponse]
