from functools import lru_cache

from pydantic import Field
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
