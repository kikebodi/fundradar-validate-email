"""
Concrete EmailSender backed by the Resend HTTP API.

Owns the httpx.AsyncClient lifecycle. Retries on transient failures
(transport errors, 429, 5xx) with exponential backoff; surfaces a clean
EmailSendError on terminal failure.
"""

from __future__ import annotations

import asyncio
import logging

import httpx

from business.interfaces.email_sender import EmailSender, EmailSendError
from domain.models.email import EmailMessage, SendResult

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


class ResendEmailSender(EmailSender):
    BASE_URL = "https://api.resend.com"
    EMAILS_PATH = "/emails"

    def __init__(
        self,
        api_key: str,
        timeout: float = 10.0,
        max_retries: int = 3,
    ) -> None:
        self._max_retries = max_retries
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=httpx.Timeout(timeout, connect=5.0),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def send(self, message: EmailMessage) -> SendResult:
        payload = {
            "from": message.sender,
            "to": [message.recipient],
            "subject": message.subject,
            "html": message.html_body,
        }

        attempt = 0
        backoff = 0.5
        while True:
            attempt += 1
            try:
                response = await self._client.post(self.EMAILS_PATH, json=payload)
            except httpx.TransportError as exc:
                if attempt >= self._max_retries:
                    logger.error(
                        "resend_transport_error_exhausted attempts=%d error=%s",
                        attempt,
                        exc.__class__.__name__,
                    )
                    raise EmailSendError(f"transport error: {exc}") from exc
                await asyncio.sleep(backoff)
                backoff *= 2
                continue

            if response.status_code < 300:
                provider_id = str(response.json().get("id", ""))
                return SendResult(provider_message_id=provider_id)

            if response.status_code in _RETRYABLE_STATUS and attempt < self._max_retries:
                await asyncio.sleep(backoff)
                backoff *= 2
                continue

            logger.error(
                "resend_send_failed status=%d body=%s",
                response.status_code,
                response.text[:512],
            )
            raise EmailSendError(
                f"resend send failed: {response.status_code}",
                status_code=response.status_code,
            )
