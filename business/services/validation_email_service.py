"""
ValidationEmailService — orchestrates building and sending the validation
email when a new company is registered.

Depends only on the EmailSender + TemplateRenderer ports. Concrete
adapters are injected by business/factory.py.
"""

from __future__ import annotations

import logging

from business.interfaces.email_sender import EmailSender
from business.interfaces.template_renderer import TemplateRenderer
from domain.models.company import Company
from domain.models.email import EmailMessage, SendResult, ValidationLinks

logger = logging.getLogger(__name__)

TEMPLATE_NAME = "validate_email_template.html"
SUBJECT = "Confirm your FundRadar account"


class ValidationEmailService:
    def __init__(
        self,
        sender: EmailSender,
        renderer: TemplateRenderer,
        from_email: str,
        base_url: str,
    ) -> None:
        self._sender = sender
        self._renderer = renderer
        self._from_email = from_email
        self._base_url = base_url.rstrip("/")

    def _build_links(self, company_id: str) -> ValidationLinks:
        return ValidationLinks(
            validate_url=f"{self._base_url}/validate?id={company_id}",  # type: ignore[arg-type]
            unsubscribe_url=f"{self._base_url}/unsubscribe?id={company_id}",  # type: ignore[arg-type]
        )

    def _render(self, company: Company, links: ValidationLinks) -> str:
        return self._renderer.render(
            TEMPLATE_NAME,
            {
                "client_id": str(company.id),
                "client_name": company.name,
                "validate_url": str(links.validate_url),
                "unsubscribe_url": str(links.unsubscribe_url),
            },
        )

    async def send_validation_email(self, company: Company) -> SendResult:
        links = self._build_links(str(company.id))
        html = self._render(company, links)
        message = EmailMessage(
            sender=self._from_email,
            recipient=company.email,
            subject=SUBJECT,
            html_body=html,
        )
        result = await self._sender.send(message)
        logger.info(
            "validation_email_sent company_id=%s message_id=%s",
            company.id,
            result.provider_message_id,
        )
        return result
