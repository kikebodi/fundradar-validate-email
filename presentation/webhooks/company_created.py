"""
Presentation — Supabase webhook for newly created companies.

Responsibilities (and ONLY these):
  - Validate the incoming Supabase webhook payload
  - Map the transport DTO to the domain Company entity
  - Delegate to ValidationEmailService
  - Translate domain/business errors into HTTP responses

No template rendering, no provider calls, no business decisions here.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status

from business.interfaces.email_sender import EmailSendError
from domain.models.company import Company
from presentation.dependencies import ValidationEmailServiceDep
from presentation.webhooks.schemas import CompanyCreatedWebhook, WebhookAck

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/supabase", tags=["webhooks"])


@router.post(
    "/company-created",
    response_model=WebhookAck,
    status_code=status.HTTP_202_ACCEPTED,
)
async def company_created(
    payload: CompanyCreatedWebhook,
    service: ValidationEmailServiceDep,
) -> WebhookAck:
    record = payload.record
    company = Company(id=record.id, email=record.email, name=record.name)
    logger.info("webhook_received company_id=%s", company.id)

    try:
        result = await service.send_validation_email(company)
    except EmailSendError as exc:
        logger.error(
            "email_send_error company_id=%s status=%s",
            company.id,
            exc.status_code,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="email provider failure",
        ) from exc

    return WebhookAck(message_id=result.provider_message_id)
