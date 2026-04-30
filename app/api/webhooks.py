from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import EmailServiceDep
from app.clients.resend_client import ResendError
from app.core.logging import get_logger
from app.models.webhooks import CompanyCreatedWebhook, WebhookAck

logger = get_logger(__name__)

router = APIRouter(prefix="/webhooks/supabase", tags=["webhooks"])


@router.post(
    "/company-created",
    response_model=WebhookAck,
    status_code=status.HTTP_202_ACCEPTED,
)
async def company_created(
    payload: CompanyCreatedWebhook,
    service: EmailServiceDep,
) -> WebhookAck:
    record = payload.record
    try:
        result = await service.send_validation_email(
            recipient=record.email,
            client_id=record.id,
            client_name=record.name,
        )
    except ResendError as exc:
        logger.error("resend_error client_id=%s status=%s", record.id, exc.status_code)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="email provider failure",
        ) from exc

    return WebhookAck(message_id=result.id)
