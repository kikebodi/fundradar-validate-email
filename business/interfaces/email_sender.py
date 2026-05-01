"""
EmailSender port — contract for any transactional email provider.

Concrete adapters live in business/services/. The orchestrator
(ValidationEmailService) depends only on this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from domain.models.email import EmailMessage, SendResult


class EmailSendError(Exception):
    """Raised when the provider rejects the send after retries are exhausted."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class EmailSender(ABC):
    @abstractmethod
    async def send(self, message: EmailMessage) -> SendResult: ...

    @abstractmethod
    async def aclose(self) -> None: ...

    async def __aenter__(self) -> "EmailSender":
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self.aclose()
