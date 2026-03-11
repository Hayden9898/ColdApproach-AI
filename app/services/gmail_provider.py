"""
Gmail API email provider using OAuth2 tokens.
Sends email as the authenticated user — appears in their Sent folder.
"""

import base64
import os
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from typing import Any, Dict, List, Optional, Tuple

from app.services.email_provider import EmailProvider
from app.utils.token_store import get_token, save_token


class GmailProvider(EmailProvider):

    def _get_gmail_service(self, from_email: str):
        """Build a Gmail API service object from the stored OAuth token."""
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        token_data = get_token(from_email)
        if not token_data:
            raise ValueError(
                f"No OAuth token for {from_email}. Complete /auth/gmail/login first."
            )

        creds = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.environ.get("GOOGLE_CLIENT_ID"),
            client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
            scopes=["https://www.googleapis.com/auth/gmail.compose"],
        )

        # Refresh expired token
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request

            creds.refresh(Request())
            save_token(from_email, {
                "access_token": creds.token,
                "refresh_token": creds.refresh_token,
                "provider": "gmail",
            })

        return build("gmail", "v1", credentials=creds)

    def _build_raw_message(
        self,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        reply_to: Optional[str] = None,
        html_body: Optional[str] = None,
        attachments: Optional[List[Tuple[str, bytes, str]]] = None,
    ) -> str:
        """Build a MIME message and return its base64url-encoded raw string."""
        if html_body and attachments:
            message = MIMEMultipart("mixed")
            alt = MIMEMultipart("alternative")
            alt.attach(MIMEText(body, "plain"))
            alt.attach(MIMEText(html_body, "html"))
            message.attach(alt)
            for filename, file_bytes, mime_type in attachments:
                maintype, subtype = mime_type.split("/", 1)
                part = MIMEBase(maintype, subtype)
                part.set_payload(file_bytes)
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", "attachment", filename=filename)
                message.attach(part)
        elif html_body:
            message = MIMEMultipart("alternative")
            message.attach(MIMEText(body, "plain"))
            message.attach(MIMEText(html_body, "html"))
        else:
            message = MIMEText(body)

        message["to"] = to_email
        message["from"] = from_email
        message["subject"] = subject
        if reply_to:
            message["Reply-To"] = reply_to

        return base64.urlsafe_b64encode(message.as_bytes()).decode()

    def send(
        self,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        reply_to: Optional[str] = None,
        html_body: Optional[str] = None,
        attachments: Optional[List[Tuple[str, bytes, str]]] = None,
    ) -> Dict[str, Any]:
        try:
            service = self._get_gmail_service(from_email)
            raw = self._build_raw_message(
                from_email, to_email, subject, body, reply_to, html_body, attachments
            )
            result = (
                service.users()
                .messages()
                .send(userId="me", body={"raw": raw})
                .execute()
            )
            return {
                "success": True,
                "message_id": result.get("id"),
                "error": None,
            }
        except Exception as exc:
            return {"success": False, "message_id": None, "error": str(exc)}

    def create_draft(
        self,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        reply_to: Optional[str] = None,
        html_body: Optional[str] = None,
        attachments: Optional[List[Tuple[str, bytes, str]]] = None,
    ) -> Dict[str, Any]:
        """Create a Gmail draft. Returns draft_id for later sending."""
        try:
            service = self._get_gmail_service(from_email)
            raw = self._build_raw_message(
                from_email, to_email, subject, body, reply_to, html_body, attachments
            )
            result = (
                service.users()
                .drafts()
                .create(userId="me", body={"message": {"raw": raw}})
                .execute()
            )
            return {
                "success": True,
                "draft_id": result.get("id"),
                "error": None,
            }
        except Exception as exc:
            return {"success": False, "draft_id": None, "error": str(exc)}

    def send_draft(
        self,
        from_email: str,
        draft_id: str,
    ) -> Dict[str, Any]:
        """Send an existing Gmail draft by ID."""
        try:
            service = self._get_gmail_service(from_email)
            result = (
                service.users()
                .drafts()
                .send(userId="me", body={"id": draft_id})
                .execute()
            )
            return {
                "success": True,
                "message_id": result.get("id"),
                "error": None,
            }
        except Exception as exc:
            return {"success": False, "message_id": None, "error": str(exc)}

    def validate_sender(self, from_email: str) -> Dict[str, Any]:
        token_data = get_token(from_email)
        if token_data:
            return {"verified": True, "detail": "OAuth token exists."}
        return {
            "verified": False,
            "detail": "No OAuth token. Complete /auth/gmail/login first.",
        }

    def provider_name(self) -> str:
        return "gmail"
