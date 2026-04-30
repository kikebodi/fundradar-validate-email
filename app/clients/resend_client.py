from __future__ import annotations

import asyncio

import httpx

from app.core.logging import get_logger
from app.models.email import ResendEmailRequest, ResendEmailResponse

logger = get_logger(__name__)


class ResendError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ResendClient:
    BASE_URL = "https://api.resend.com"
    EMAILS_PATH = "/emails"

    def __init__(
        self,
        api_key: str,
        timeout: float = 10.0,
        max_retries: int = 3,
    ) -> None:
        self._api_key = api_key
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

    async def send_email(self, request: ResendEmailRequest) -> ResendEmailResponse:
        payload = request.model_dump(by_alias=True, exclude_none=True)
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
                    raise ResendError(f"transport error: {exc}") from exc
                await asyncio.sleep(backoff)
                backoff *= 2
                continue

            if response.status_code < 300:
                return ResendEmailResponse.model_validate(response.json())

            if response.status_code in {429, 500, 502, 503, 504} and attempt < self._max_retries:
                await asyncio.sleep(backoff)
                backoff *= 2
                continue

            logger.error(
                "resend_send_failed status=%d body=%s",
                response.status_code,
                response.text[:512],
            )
            raise ResendError(
                f"resend send failed: {response.status_code}",
                status_code=response.status_code,
            )
