from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ResendEmailRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sender: str = Field(alias="from")
    to: list[EmailStr]
    subject: str
    html: str
    reply_to: str | None = Field(default=None, alias="reply_to")


class ResendEmailResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
