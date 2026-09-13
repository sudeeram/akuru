from app.ai.base import AIProvider, AIProviderError
from app.ai.fake import FakeAIProvider
from app.ai.provider import OpenAIProvider
from app.config import Settings


def build_ai_provider(settings: Settings) -> AIProvider:
    if settings.ai_provider == "fake":
        return FakeAIProvider()
    if settings.ai_provider == "openai":
        assert settings.openai_api_key and settings.openai_model
        return OpenAIProvider(
            api_key=settings.openai_api_key.get_secret_value(), model=settings.openai_model,
            timeout_seconds=settings.ai_timeout_seconds, max_retries=settings.ai_max_retries,
            max_concurrency=settings.ai_max_concurrency, max_pages=settings.ai_max_pages_per_request,
            max_input_characters=settings.ai_max_input_characters,
            max_image_bytes=settings.ai_max_image_bytes, max_output_tokens=settings.ai_max_output_tokens,
        )
    raise AIProviderError("ai_provider_disabled", "The AI provider is not enabled.")
