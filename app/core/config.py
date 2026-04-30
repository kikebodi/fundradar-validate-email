from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    resend_api_key: str = Field(..., alias="RESEND_API_KEY")
    from_email: str = Field(..., alias="FROM_EMAIL")
    base_url: str = Field("https://fundradar.ai", alias="BASE_URL")
    webhook_secret: str | None = Field(default=None, alias="SUPABASE_WEBHOOK_SECRET")
    request_timeout: float = Field(default=10.0, alias="REQUEST_TIMEOUT")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
