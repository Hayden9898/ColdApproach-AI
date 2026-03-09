# Pydantic schemas/models

from datetime import datetime
from typing import Dict, List, Optional

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
    smooth_grammar: bool = True              # allow GPT to smooth grammar around placeholders


# ---------------------------------------------------------------------------
# Email sending
# ---------------------------------------------------------------------------

class SendEmailRequest(BaseModel):
    from_email: str                            # sender email (determines provider)
    to_email: str                              # recipient email
    subject: str
    body: str
    reply_to: Optional[str] = None
    html_body: Optional[str] = None            # HTML version of the email body
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


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

BATCH_LIMIT = 20

class BatchSubmitRequest(BaseModel):
    urls: List[str]                            # company URLs (max 20)
    from_email: str                            # sender email (determines provider)
    resume_id: Optional[str] = None
    resume_profile: Optional[dict] = None
    mode: str = "template"
    template: Optional[str] = None
    subject_template: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    smooth_grammar: bool = True
    send_at: Optional[datetime] = None         # None = send after generation, set = schedule all

    @field_validator("send_at", mode="before")
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v


class BatchStatusResponse(BaseModel):
    job_id: str
    status: str                                # queued | processing | completed | failed
    total: int
    completed: int
    failed: int
    results: Dict
