import base64
import time
from threading import BoundedSemaphore
from typing import Any

from openai import APIConnectionError, APITimeoutError, AuthenticationError, InternalServerError, OpenAI, RateLimitError
from pydantic import ValidationError

from app.ai.base import AIProviderError, AIRequest, AIResult, AIUsage, AI_PURPOSES


_TRANSIENT = (APIConnectionError, APITimeoutError, InternalServerError)


class OpenAIProvider:
    name = "openai"

    def __init__(
        self, *, api_key: str, model: str, timeout_seconds: float, max_retries: int,
        max_concurrency: int, max_pages: int, max_input_characters: int,
        max_image_bytes: int, max_output_tokens: int, client: Any | None = None,
    ):
        self.model = model
        self.max_retries = max_retries
        self.max_pages = max_pages
        self.max_input_characters = max_input_characters
        self.max_image_bytes = max_image_bytes
        self.max_output_tokens = max_output_tokens
        self._semaphore = BoundedSemaphore(max_concurrency)
        self._client = client or OpenAI(
            api_key=api_key, timeout=timeout_seconds, max_retries=0,
        )

    def generate(self, request: AIRequest) -> AIResult:
        self._validate(request)
        content: list[dict[str, str]] = [{"type": "input_text", "text": request.task}]
        for page in request.pages:
            content.append({
                "type": "input_text",
                "text": f"<source_page number=\"{page.page_number}\">\n{page.text}\n</source_page>",
            })
            if page.image_data_url:
                content.append({"type": "input_image", "image_url": page.image_data_url, "detail": "high"})

        started = time.monotonic()
        last_error: Exception | None = None
        attempts = 0
        with self._semaphore:
            for attempts in range(1, self.max_retries + 2):
                try:
                    response = self._client.responses.parse(
                        model=self.model,
                        instructions=request.instructions,
                        input=[{"role": "user", "content": content}],
                        text_format=request.output_type,
                        max_output_tokens=self.max_output_tokens,
                        metadata={
                            **request.metadata,
                            "purpose": request.purpose,
                            "prompt": request.prompt_name,
                            "prompt_version": request.prompt_version,
                        },
                        store=False,
                    )
                    output = getattr(response, "output_parsed", None)
                    if output is None:
                        raise AIProviderError("invalid_ai_output", "The AI response did not contain valid structured output.")
                    try:
                        output = request.output_type.model_validate(output)
                    except ValidationError as exc:
                        raise AIProviderError(
                            "invalid_ai_output", "The AI response did not match the required schema."
                        ) from exc
                    usage = getattr(response, "usage", None)
                    return AIResult(
                        output=output, provider=self.name, model=self.model,
                        response_id=getattr(response, "id", None),
                        usage=AIUsage(
                            input_tokens=getattr(usage, "input_tokens", None),
                            output_tokens=getattr(usage, "output_tokens", None),
                            total_tokens=getattr(usage, "total_tokens", None),
                        ),
                        latency_ms=round((time.monotonic() - started) * 1000),
                        attempt_count=attempts,
                    )
                except AIProviderError:
                    raise
                except AuthenticationError as exc:
                    raise AIProviderError(
                        "invalid_credential", "The provider credential is invalid.",
                        failover_allowed=True, disable_account=True,
                    ) from exc
                except RateLimitError as exc:
                    body = exc.body if isinstance(exc.body, dict) else {}
                    code = body.get("code") or (
                        body.get("error", {}).get("code") if isinstance(body.get("error"), dict) else None
                    )
                    if code == "credit_balance_exhausted":
                        raise AIProviderError(
                            "credit_balance_exhausted", "The provider account has exhausted its credit.",
                            failover_allowed=True,
                        ) from exc
                    last_error = exc
                    if attempts > self.max_retries:
                        break
                    time.sleep(min(0.25 * (2 ** (attempts - 1)), 1.0))
                except _TRANSIENT as exc:
                    last_error = exc
                    if attempts > self.max_retries:
                        break
                    time.sleep(min(0.25 * (2 ** (attempts - 1)), 1.0))
                except Exception as exc:
                    raise AIProviderError("ai_provider_error", "The AI provider request failed.") from exc
        raise AIProviderError(
            "ai_provider_unavailable", "The AI provider is temporarily unavailable.",
            failover_allowed=True, cooldown_seconds=60,
        ) from last_error

    def _validate(self, request: AIRequest) -> None:
        if request.purpose not in AI_PURPOSES:
            raise AIProviderError("invalid_ai_purpose", "The requested AI operation is not supported.")
        if len(request.metadata) > 13 or any(
            len(str(key)) > 64 or len(str(value)) > 512
            for key, value in request.metadata.items()
        ):
            raise AIProviderError("invalid_ai_metadata", "The AI request metadata is invalid.")
        if len(request.pages) > self.max_pages:
            raise AIProviderError("ai_page_limit", "The AI request contains too many pages.")
        characters = len(request.task) + sum(len(page.text) for page in request.pages)
        if characters > self.max_input_characters:
            raise AIProviderError("ai_input_limit", "The AI request contains too much text.")
        image_bytes = 0
        for page in request.pages:
            if page.page_number < 1:
                raise AIProviderError("invalid_source_page", "Source page numbers must be positive.")
            if page.image_data_url:
                try:
                    header, encoded = page.image_data_url.split(",", 1)
                    if not header.startswith("data:image/") or ";base64" not in header:
                        raise ValueError
                    image_bytes += len(base64.b64decode(encoded, validate=True))
                except (ValueError, TypeError) as exc:
                    raise AIProviderError("invalid_source_image", "A source page image is invalid.") from exc
        if image_bytes > self.max_image_bytes:
            raise AIProviderError("ai_image_limit", "The AI request contains too much image data.")
