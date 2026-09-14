from dataclasses import dataclass, field
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel


OutputT = TypeVar("OutputT", bound=BaseModel)
AI_PURPOSES = frozenset({
    "textbook_extraction", "paper_extraction", "unit_mapping", "assessment", "tutoring", "illustration"
})


class AIProviderError(RuntimeError):
    """A safe provider failure that callers may record without leaking source content."""

    def __init__(
        self, code: str, message: str, *, failover_allowed: bool = False,
        disable_account: bool = False, cooldown_seconds: int | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.failover_allowed = failover_allowed
        self.disable_account = disable_account
        self.cooldown_seconds = cooldown_seconds


@dataclass(frozen=True)
class SourcePage:
    page_number: int
    text: str = ""
    image_data_url: str | None = None


@dataclass(frozen=True)
class AIRequest:
    purpose: str
    prompt_name: str
    prompt_version: str
    instructions: str
    task: str
    output_type: type[OutputT]
    pages: tuple[SourcePage, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AIUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class AIResult:
    output: BaseModel
    provider: str
    model: str
    response_id: str | None
    usage: AIUsage
    latency_ms: int
    attempt_count: int


class AIProvider(Protocol):
    name: str
    model: str

    def generate(self, request: AIRequest) -> AIResult: ...
