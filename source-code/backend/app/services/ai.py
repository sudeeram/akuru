import uuid
from datetime import datetime, timezone
import time

from sqlalchemy.orm import Session

from app.ai.base import AIProvider, AIProviderError, AIRequest, AIResult
from app.models import AIInvocation


class AIService:
    def __init__(self, db: Session, provider: AIProvider):
        self.db = db
        self.provider = provider

    def generate(
        self, request: AIRequest, *, actor_id: uuid.UUID | None = None,
        document_version_id: uuid.UUID | None = None,
    ) -> AIResult:
        invocation = AIInvocation(
            actor_id=actor_id, document_version_id=document_version_id,
            provider=self.provider.name, model=self.provider.model, purpose=request.purpose,
            prompt_name=request.prompt_name, prompt_version=request.prompt_version,
            schema_name=request.output_type.__name__, status="processing",
            request_metadata={
                "page_numbers": [page.page_number for page in request.pages],
                "page_count": len(request.pages),
            },
        )
        self.db.add(invocation)
        self.db.flush()
        started = time.monotonic()
        try:
            result = self.provider.generate(request)
        except AIProviderError as exc:
            invocation.status = "failed"
            invocation.error_code = exc.code
            invocation.latency_ms = round((time.monotonic() - started) * 1000)
            invocation.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            raise
        invocation.status = "completed"
        invocation.response_id = result.response_id
        invocation.latency_ms = result.latency_ms
        invocation.input_tokens = result.usage.input_tokens
        invocation.output_tokens = result.usage.output_tokens
        invocation.total_tokens = result.usage.total_tokens
        invocation.attempt_count = result.attempt_count
        invocation.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        return result
