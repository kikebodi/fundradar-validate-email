"""
Presentation-layer dependency providers.

The orchestrator is constructed in main.py during the app lifespan and
attached to app.state. Routes pull it through these typed Depends helpers.
"""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import Depends, Request

from business.services.validation_email_service import ValidationEmailService


def get_validation_email_service(request: Request) -> ValidationEmailService:
    service = getattr(request.app.state, "validation_email_service", None)
    if service is None:
        raise RuntimeError("validation_email_service is not initialized")
    return cast(ValidationEmailService, service)


ValidationEmailServiceDep = Annotated[
    ValidationEmailService,
    Depends(get_validation_email_service),
]
