from __future__ import annotations

from typing import Annotated, cast

from fastapi import Depends, Request

from app.services.protocols import SendsValidationEmail


def get_email_service(request: Request) -> SendsValidationEmail:
    service = getattr(request.app.state, "email_service", None)
    if service is None:
        raise RuntimeError("email_service is not initialized")
    return cast(SendsValidationEmail, service)


EmailServiceDep = Annotated[SendsValidationEmail, Depends(get_email_service)]
