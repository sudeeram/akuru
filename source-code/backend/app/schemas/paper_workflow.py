"""Read-only, server-derived Admin workflow summaries."""
from typing import Literal
from pydantic import BaseModel, Field

class WorkflowStep(BaseModel):
    number: int
    label: str
    state: Literal['not_started', 'processing', 'attention', 'complete']
    completed: int
    checked: int | None = None
    total: int
    detail: str
    href: str

class WorkflowScope(BaseModel):
    paperId: str | None
    paperTitle: str
    steps: list[WorkflowStep]
    excluded: int = 0
    formalExamPublished: bool = False

class DocumentWorkflow(BaseModel):
    documentId: str
    scopes: list[WorkflowScope]

class WorkflowResponse(BaseModel):
    policy: str = 'past-paper-workflow-v1'
    documents: list[DocumentWorkflow] = Field(default_factory=list)
