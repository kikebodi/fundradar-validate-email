"""
Presentation-layer dependency providers.

The orchestrator is constructed in main.py during the app lifespan and
attached to app.state. Routes pull it through these typed Depends helpers.
If the email subsystem failed to start (e.g. missing RESEND_API_KEY on
Railway boot), the dependency raises 503 so the healthcheck path can
still respond OK.
"""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request, status

from business.services.validation_email_service import ValidationEmailService


def get_validation_email_service(request: Request) -> ValidationEmailService:
    service = getattr(request.app.state, "validation_email_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="email subsystem is not configured",
        )
    return cast(ValidationEmailService, service)


ValidationEmailServiceDep = Annotated[
    ValidationEmailService,
    Depends(get_validation_email_service),
]
