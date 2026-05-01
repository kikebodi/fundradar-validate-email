"""
FundRadar Validation Email API — entry point.

Layer map:
  Presentation  →  presentation/webhooks/, presentation/api/
  Business      →  business/services/ + business/interfaces/ + business/factory.py
  Domain        →  domain/models/
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from business.config.settings import get_settings
from business.factory import build_email_sender, build_validation_email_service
from presentation.api.health import router as health_router
from presentation.webhooks.company_created import router as company_created_router

logger = logging.getLogger(__name__)


def _configure_logging(level: str) -> None:
    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    _configure_logging(settings.log_level)

    app.state.email_sender = None
    app.state.validation_email_service = None

    try:
        sender = build_email_sender(settings)
        service = build_validation_email_service(sender, settings)
    except RuntimeError as exc:
        logger.warning(
            "startup_skipped_email_subsystem reason=%s — webhook will return 503 "
            "until RESEND_API_KEY and FROM_EMAIL are set",
            exc,
        )
        sender = None
        service = None
    else:
        app.state.email_sender = sender
        app.state.validation_email_service = service
        logger.info("startup_complete base_url=%s", settings.base_url)

    try:
        yield
    finally:
        if sender is not None:
            await sender.aclose()
        logger.info("shutdown_complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="FundRadar Validation Email API",
        description="Sends a validation email when a new company is registered.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.include_router(health_router)
    app.include_router(company_created_router)

    @app.get("/", tags=["health"])
    async def root() -> dict[str, str]:
        return {"status": "ok", "service": "fundradar-validate-email"}

    return app


app: FastAPI = create_app()
