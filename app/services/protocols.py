from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.models.email import ResendEmailResponse


class SendsValidationEmail(Protocol):
    async def send_validation_email(
        self,
        *,
        recipient: str,
        client_id: UUID,
        client_name: str | None = None,
    ) -> ResendEmailResponse: ...
