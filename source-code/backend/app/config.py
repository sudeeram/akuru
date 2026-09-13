from functools import lru_cache

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="AKURU_", extra="ignore", case_sensitive=False
    )

    environment: str = "development"
    database_host: str = "127.0.0.1"
    database_port: int = 5432
    database_name: str = "akuru"
    database_user: str = "postgres"
    database_password: str = Field(repr=False)
    cors_origins: list[str] = [
        "http://localhost:5180", "http://127.0.0.1:5180",
        "http://localhost:5181", "http://127.0.0.1:5181",
    ]
    allowed_hosts: list[str] = ["localhost", "127.0.0.1"]
    cookie_secure: bool = False
    session_hours: int = Field(default=12, ge=1, le=168)
    login_attempt_limit: int = Field(default=8, ge=3, le=50)
    login_window_minutes: int = Field(default=15, ge=1, le=60)
    login_lock_minutes: int = Field(default=15, ge=1, le=1440)
    storage_backend: str = "local"
    local_storage_path: str = "/data/akuru/documents"
    max_document_bytes: int = Field(default=50 * 1024 * 1024, ge=1024, le=250 * 1024 * 1024)
    oci_object_namespace: str | None = None
    oci_object_bucket: str | None = None
    redis_url: str = Field(default="redis://127.0.0.1:6379/0", repr=False)
    document_queue_name: str = "akuru:documents"
    document_job_timeout_seconds: int = Field(default=120, ge=5, le=3600)
    document_job_memory_mb: int = Field(default=512, ge=128, le=4096)
    document_max_pages: int = Field(default=500, ge=1, le=2000)
    extraction_version: str = "deterministic-v1"
    document_render_dpi: int = Field(default=180, ge=96, le=300)
    document_ocr_min_characters: int = Field(default=40, ge=0, le=1000)
    tesseract_command: str = "tesseract"
    ai_provider: str = "disabled"
    openai_api_key: SecretStr | None = Field(default=None, repr=False)
    openai_model: str | None = None
    openai_account_keys: dict[str, SecretStr] = Field(default_factory=dict, repr=False)
    ai_timeout_seconds: float = Field(default=45, ge=5, le=180)
    ai_max_retries: int = Field(default=2, ge=0, le=3)
    ai_max_concurrency: int = Field(default=2, ge=1, le=16)
    ai_max_pages_per_request: int = Field(default=8, ge=1, le=30)
    ai_max_input_characters: int = Field(default=80_000, ge=1_000, le=500_000)
    ai_max_image_bytes: int = Field(default=20 * 1024 * 1024, ge=1024, le=100 * 1024 * 1024)
    ai_max_output_tokens: int = Field(default=4_000, ge=100, le=32_000)
    embedding_provider: str = "local"
    embedding_model: str = "akuru-local-v1"
    embedding_dimensions: int = Field(default=256, ge=64, le=3072)

    @model_validator(mode="after")
    def validate_ai_provider(self) -> "Settings":
        if self.ai_provider not in {"disabled", "fake", "openai"}:
            raise ValueError("AKURU_AI_PROVIDER must be disabled, fake, or openai")
        if self.ai_provider == "openai" and (not self.openai_api_key or not self.openai_model):
            raise ValueError(
                "AKURU_OPENAI_API_KEY and AKURU_OPENAI_MODEL are required when AKURU_AI_PROVIDER=openai"
            )
        if self.embedding_provider not in {"local", "openai"}:
            raise ValueError("AKURU_EMBEDDING_PROVIDER must be local or openai")
        if self.embedding_dimensions != 256:
            raise ValueError("AKURU_EMBEDDING_DIMENSIONS must remain 256 for the current database schema")
        if self.embedding_provider == "openai" and not self.openai_api_key:
            raise ValueError("AKURU_OPENAI_API_KEY is required when AKURU_EMBEDDING_PROVIDER=openai")
        return self

    def openai_account_key(self, alias: str) -> str | None:
        secret = self.openai_account_keys.get(alias.upper())
        return secret.get_secret_value() if secret else None

    @property
    def database_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.database_user,
            password=self.database_password,
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
        )

    @property
    def server_database_url(self) -> URL:
        return self.database_url.set(database="postgres")


@lru_cache
def get_settings() -> Settings:
    return Settings()
