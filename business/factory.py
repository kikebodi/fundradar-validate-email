"""
Dependency factory — wires production adapters from settings.

Presentation calls build_validation_email_service() during app startup.
Tests bypass the factory and inject doubles directly.
"""

from __future__ import annotations

from business.config.settings import Settings, get_settings
from business.interfaces.email_sender import EmailSender
from business.services.jinja_template_renderer import JinjaTemplateRenderer
from business.services.resend_email_sender import ResendEmailSender
from business.services.validation_email_service import ValidationEmailService


def build_email_sender(settings: Settings | None = None) -> EmailSender:
    cfg = settings or get_settings()
    if not cfg.resend_api_key:
        raise RuntimeError(
            "RESEND_API_KEY is not set — cannot construct ResendEmailSender."
        )
    return ResendEmailSender(
        api_key=cfg.resend_api_key,
        timeout=cfg.request_timeout,
        max_retries=cfg.max_retries,
    )


def build_validation_email_service(
    sender: EmailSender,
    settings: Settings | None = None,
) -> ValidationEmailService:
    cfg = settings or get_settings()
    if not cfg.from_email:
        raise RuntimeError(
            "FROM_EMAIL is not set — cannot construct ValidationEmailService."
        )
    return ValidationEmailService(
        sender=sender,
        renderer=JinjaTemplateRenderer(),
        from_email=cfg.from_email,
        base_url=cfg.base_url,
    )
