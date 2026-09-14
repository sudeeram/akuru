import base64
import time
from dataclasses import dataclass
from typing import Any
from openai import APIConnectionError, APITimeoutError, AuthenticationError, InternalServerError, OpenAI, RateLimitError
from app.ai.base import AIProviderError

@dataclass(frozen=True)
class ImageResult:
    content: bytes
    content_type: str
    provider: str
    model: str
    response_id: str | None
    latency_ms: int

class OpenAIImageProvider:
    def __init__(self, api_key: str, model: str, size: str, timeout_seconds: float, client: Any | None = None):
        self.model, self.size = model, size
        self.client = client or OpenAI(api_key=api_key, timeout=timeout_seconds, max_retries=0)

    def generate(self, prompt: str) -> ImageResult:
        started = time.monotonic()
        try:
            response = self.client.images.generate(model=self.model, prompt=prompt, size=self.size,
                quality="low", output_format="png", n=1)
            encoded = response.data[0].b64_json
            if not encoded: raise AIProviderError("invalid_image_output", "The image provider returned no image.")
            return ImageResult(base64.b64decode(encoded, validate=True), "image/png", "openai", self.model,
                getattr(response, "id", None), round((time.monotonic() - started) * 1000))
        except AuthenticationError as exc:
            raise AIProviderError("invalid_credential", "The provider credential is invalid.", failover_allowed=True, disable_account=True) from exc
        except RateLimitError as exc:
            body = exc.body if isinstance(exc.body, dict) else {}
            code = body.get("code") or (body.get("error", {}).get("code") if isinstance(body.get("error"), dict) else None)
            if code == "credit_balance_exhausted":
                raise AIProviderError("credit_balance_exhausted", "The provider account has exhausted its credit.", failover_allowed=True) from exc
            raise AIProviderError("image_provider_rate_limited", "The image provider is temporarily rate limited.", failover_allowed=True, cooldown_seconds=60) from exc
        except (APIConnectionError, APITimeoutError, InternalServerError) as exc:
            raise AIProviderError("image_provider_unavailable", "The image provider is temporarily unavailable.", failover_allowed=True, cooldown_seconds=60) from exc
        except AIProviderError: raise
        except Exception as exc:
            raise AIProviderError("image_provider_error", "The image provider request failed.") from exc
