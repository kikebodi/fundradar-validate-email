"""
Domain entity for a company registered on FundRadar.

Pure data — no framework, no I/O. Pydantic v2 only.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class Company(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    id: UUID
    email: EmailStr
    name: str | None = None
