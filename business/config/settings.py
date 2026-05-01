"""
Application configuration.

Loads from `.env` at the repo root and from shell environment variables.
`.env` wins over the shell when both define the same key, so a value
exported by an activation hook cannot shadow the value committed in `.env`.
A key absent from `.env` falls back to the shell — this is what makes the
service work on Railway, where every variable comes from the platform.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values
from pydantic import BaseModel, Field

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseModel):
    """Typed view of the values loaded from `.env`."""

    resend_api_key: str = Field(default="", description="Resend API key")
    from_email: str = Field(
        default="",
        description="Sender header, e.g. 'FundRadar <noreply@fundradar.ai>'",
    )
    base_url: str = Field(default="https://fundradar.ai")

    request_timeout: float = Field(default=10.0, ge=0)
    max_retries: int = Field(default=3, ge=1)

    log_level: str = Field(default="INFO")
    webhook_secret: str = Field(default="")


def _load_settings() -> Settings:
    field_names = set(Settings.model_fields)

    kwargs: dict[str, str] = {
        name: os.environ[name.upper()].strip()
        for name in field_names
        if os.environ.get(name.upper(), "").strip() != ""
    }

    raw = dotenv_values(_ENV_FILE)
    for key, value in raw.items():
        lowered = key.lower()
        if value and lowered in field_names:
            stripped = value.strip()
            if stripped:
                kwargs[lowered] = stripped

    return Settings(**kwargs)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return _load_settings()
