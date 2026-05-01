"""
Domain value objects for outbound email.

These describe what the system wants to send, independent of any
provider (Resend, SES, etc.).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, HttpUrl


class ValidationLinks(BaseModel):
    model_config = ConfigDict(frozen=True)

    validate_url: HttpUrl
    unsubscribe_url: HttpUrl


class EmailMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    sender: str
    recipient: EmailStr
    subject: str
    html_body: str


class SendResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider_message_id: str
