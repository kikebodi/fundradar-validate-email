"""
Transport DTOs for the Supabase webhook.

These describe the wire shape Supabase sends and the response we return.
Kept in the presentation layer because they're a transport contract,
not part of the domain.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CompanyRecordDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: UUID
    email: EmailStr
    name: str | None = None


class CompanyCreatedWebhook(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: Literal["INSERT"]
    table: Literal["companies"]
    schema_: str = Field(alias="schema")
    record: CompanyRecordDTO


class WebhookAck(BaseModel):
    status: Literal["accepted"] = "accepted"
    message_id: str | None = None
