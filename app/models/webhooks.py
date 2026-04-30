from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CompanyRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    email: EmailStr
    name: str | None = None


class CompanyCreatedWebhook(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["INSERT"]
    table: Literal["companies"]
    schema_: str = Field(alias="schema")
    record: CompanyRecord


class WebhookAck(BaseModel):
    status: Literal["accepted"] = "accepted"
    message_id: str | None = None
