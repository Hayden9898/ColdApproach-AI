# Pydantic schemas/models

from pydantic import BaseModel
from typing import Optional


class GenerateEmailRequest(BaseModel):
    url: str
    resume_id: Optional[str] = None          # pull stored profile + PDF via ID
    resume_profile: Optional[dict] = None    # fallback: pass profile directly
    mode: str = "template"                   # "template" (default) | "ml" (locked for now)
    template: Optional[str] = None           # email body template with placeholders
    subject_template: Optional[str] = None   # subject line template with placeholders
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
