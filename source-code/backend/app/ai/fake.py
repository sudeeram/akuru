import time

from pydantic import ValidationError

from app.ai.base import AIProviderError, AIRequest, AIResult, AIUsage


class FakeAIProvider:
    name = "fake"
    model = "fake-structured-v1"

    def __init__(self, response: object | None = None):
        self.response = response
        self.requests: list[AIRequest] = []

    def generate(self, request: AIRequest) -> AIResult:
        started = time.monotonic()
        self.requests.append(request)
        try:
            output = request.output_type.model_validate(self.response or {})
        except ValidationError as exc:
            raise AIProviderError(
                "invalid_ai_output", "The AI response did not match the required schema."
            ) from exc
        return AIResult(
            output=output, provider=self.name, model=self.model, response_id="fake-response",
            usage=AIUsage(input_tokens=0, output_tokens=0, total_tokens=0),
            latency_ms=round((time.monotonic() - started) * 1000), attempt_count=1,
        )
