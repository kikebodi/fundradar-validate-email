from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.webhooks import router as webhooks_router
from app.clients.resend_client import ResendClient
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.core.templates import build_template_env
from app.services.email_service import EmailService

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    settings: Settings = get_settings()

    resend_client = ResendClient(
        api_key=settings.resend_api_key,
        timeout=settings.request_timeout,
        max_retries=settings.max_retries,
    )
    email_service = EmailService(
        client=resend_client,
        env=build_template_env(),
        from_email=settings.from_email,
        base_url=settings.base_url,
    )

    app.state.resend_client = resend_client
    app.state.email_service = email_service
    logger.info("startup_complete")
    try:
        yield
    finally:
        await resend_client.aclose()
        logger.info("shutdown_complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="FundRadar Validation Email Service",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.include_router(health_router)
    app.include_router(webhooks_router)
    return app


app: FastAPI = create_app()
