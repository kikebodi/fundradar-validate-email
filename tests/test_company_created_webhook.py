from __future__ import annotations

from typing import AsyncIterator
from uuid import UUID, uuid4

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.models.email import ResendEmailResponse
from app.services.email_service import EmailService


class StubEmailService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def send_validation_email(
        self,
        *,
        recipient: str,
        client_id: UUID,
        client_name: str | None = None,
    ) -> ResendEmailResponse:
        self.calls.append(
            {
                "recipient": recipient,
                "client_id": client_id,
                "client_name": client_name,
            }
        )
        return ResendEmailResponse(id="msg_test_123")


@pytest.fixture
async def client_and_stub() -> AsyncIterator[tuple[AsyncClient, StubEmailService]]:
    app = create_app()
    stub = StubEmailService()

    async with LifespanManager(app):
        app.state.email_service = stub  # type: ignore[assignment]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac, stub


@pytest.mark.asyncio
async def test_company_created_sends_email(
    client_and_stub: tuple[AsyncClient, StubEmailService],
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
    body = response.json()
    assert body == {"status": "accepted", "message_id": "msg_test_123"}
    assert len(stub.calls) == 1
    call = stub.calls[0]
    assert call["recipient"] == "founder@example.com"
    assert call["client_id"] == company_id
    assert call["client_name"] == "Acme Inc"


@pytest.mark.asyncio
async def test_company_created_rejects_invalid_payload(
    client_and_stub: tuple[AsyncClient, StubEmailService],
) -> None:
    ac, stub = client_and_stub
    response = await ac.post(
        "/webhooks/supabase/company-created",
        json={"type": "INSERT", "table": "companies", "schema": "public", "record": {}},
    )
    assert response.status_code == 422
    assert stub.calls == []


@pytest.mark.asyncio
async def test_email_service_renders_links(
    client_and_stub: tuple[AsyncClient, StubEmailService],
) -> None:
    from app.core.templates import build_template_env

    env = build_template_env()
    template = env.get_template("validate_email_template.html")
    company_id = uuid4()
    html = template.render(
        client_id=str(company_id),
        client_name=None,
        validate_url=f"https://fundradar.ai/validate?id={company_id}",
        unsubscribe_url=f"https://fundradar.ai/unsubscribe?id={company_id}",
    )
    assert f"https://fundradar.ai/validate?id={company_id}" in html
    assert f"https://fundradar.ai/unsubscribe?id={company_id}" in html
    # ensure the type checker covers the EmailService symbol used elsewhere
    assert EmailService.__name__ == "EmailService"
