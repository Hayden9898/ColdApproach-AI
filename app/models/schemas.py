# Pydantic schemas/models

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------------
# Email generation
# ---------------------------------------------------------------------------

class GenerateEmailRequest(BaseModel):
    url: str
    resume_id: Optional[str] = None          # pull stored profile + PDF via ID
    resume_profile: Optional[dict] = None    # fallback: pass profile directly
    mode: str = "template"                   # "template" (default) | "ml" (locked for now)
    template: Optional[str] = None           # email body template with placeholders
    subject_template: Optional[str] = None   # subject line template with placeholders
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Email sending
# ---------------------------------------------------------------------------

class SendEmailRequest(BaseModel):
    from_email: str                            # sender email (determines provider)
    to_email: str                              # recipient email
    subject: str
    body: str
    reply_to: Optional[str] = None
    send_at: Optional[datetime] = None         # None = instant, set = scheduled (UTC)

    @field_validator("send_at", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v


class SendEmailResponse(BaseModel):
    success: bool
    provider: str                              # "gmail" or "ses"
    message_id: Optional[str] = None           # provider message ID (None if scheduled)
    scheduled: bool = False
    scheduled_at: Optional[str] = None         # ISO 8601 UTC
    email_id: Optional[str] = None             # UUID for scheduled emails


class SESVerifyRequest(BaseModel):
    email: str
