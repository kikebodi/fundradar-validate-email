from __future__ import annotations

from typing import AsyncIterator
from uuid import uuid4

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from business.services.jinja_template_renderer import JinjaTemplateRenderer
from domain.models.company import Company
from domain.models.email import EmailMessage, SendResult
from main import create_app


class StubEmailSender:
    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    async def send(self, message: EmailMessage) -> SendResult:
        self.sent.append(message)
        return SendResult(provider_message_id="msg_test_123")

    async def aclose(self) -> None: ...


class StubValidationEmailService:
    def __init__(self) -> None:
        self.calls: list[Company] = []

    async def send_validation_email(self, company: Company) -> SendResult:
        self.calls.append(company)
        return SendResult(provider_message_id="msg_test_123")


@pytest.fixture
async def client_and_stub() -> AsyncIterator[tuple[AsyncClient, StubValidationEmailService]]:
    app = create_app()
    stub = StubValidationEmailService()

    async with LifespanManager(app):
        app.state.validation_email_service = stub  # type: ignore[assignment]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac, stub


@pytest.mark.asyncio
async def test_company_created_sends_email(
    client_and_stub: tuple[AsyncClient, StubValidationEmailService],
) -> None:
    ac, stub = client_and_stub
    company_id = uuid4()
    payload = {
        "type": "INSERT",
        "table": "companies",
        "schema": "public",
        "record": {
            "id": str(company_id),
            "email": "founder@example.com",
            "name": "Acme Inc",
        },
    }

    response = await ac.post("/webhooks/supabase/company-created", json=payload)

    assert response.status_code == 202
    assert response.json() == {"status": "accepted", "message_id": "msg_test_123"}
    assert len(stub.calls) == 1
    company = stub.calls[0]
    assert company.id == company_id
    assert company.email == "founder@example.com"
    assert company.name == "Acme Inc"


@pytest.mark.asyncio
async def test_company_created_rejects_invalid_payload(
    client_and_stub: tuple[AsyncClient, StubValidationEmailService],
) -> None:
    ac, stub = client_and_stub
    response = await ac.post(
        "/webhooks/supabase/company-created",
        json={"type": "INSERT", "table": "companies", "schema": "public", "record": {}},
    )
    assert response.status_code == 422
    assert stub.calls == []


@pytest.mark.asyncio
async def test_validation_email_service_renders_links() -> None:
    from business.services.validation_email_service import ValidationEmailService

    sender = StubEmailSender()
    service = ValidationEmailService(
        sender=sender,
        renderer=JinjaTemplateRenderer(),
        from_email="FundRadar <noreply@fundradar.ai>",
        base_url="https://fundradar.ai",
    )
    company = Company(id=uuid4(), email="founder@example.com", name="Acme Inc")

    result = await service.send_validation_email(company)

    assert result.provider_message_id == "msg_test_123"
    assert len(sender.sent) == 1
    html = sender.sent[0].html_body
    assert f"https://fundradar.ai/validate?id={company.id}" in html
    assert f"https://fundradar.ai/unsubscribe?id={company.id}" in html
