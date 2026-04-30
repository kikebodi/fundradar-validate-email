from __future__ import annotations

from uuid import UUID

from jinja2 import Environment, Template

from app.clients.resend_client import ResendClient
from app.core.logging import get_logger
from app.models.email import ResendEmailRequest, ResendEmailResponse

logger = get_logger(__name__)

VALIDATE_TEMPLATE = "validate_email_template.html"
SUBJECT = "Confirm your FundRadar account"


class EmailService:
    def __init__(
        self,
        client: ResendClient,
        env: Environment,
        from_email: str,
        base_url: str,
    ) -> None:
        self._client = client
        self._template: Template = env.get_template(VALIDATE_TEMPLATE)
        self._from_email = from_email
        self._base_url = base_url.rstrip("/")

    async def send_validation_email(
        self,
        *,
        recipient: str,
        client_id: UUID,
        client_name: str | None = None,
    ) -> ResendEmailResponse:
        client_id_str = str(client_id)
        validate_url = f"{self._base_url}/validate?id={client_id_str}"
        unsubscribe_url = f"{self._base_url}/unsubscribe?id={client_id_str}"

        html = self._template.render(
            client_id=client_id_str,
            client_name=client_name,
            validate_url=validate_url,
            unsubscribe_url=unsubscribe_url,
        )

        request = ResendEmailRequest(
            sender=self._from_email,
            to=[recipient],
            subject=SUBJECT,
            html=html,
        )
        response = await self._client.send_email(request)
        logger.info(
            "validation_email_sent client_id=%s message_id=%s",
            client_id_str,
            response.id,
        )
        return response
