"""
Amazon SES email provider for custom domain senders.
Requires the sender email (or domain) to be verified in SES.
"""

import base64
import os
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Tuple

from app.services.email_provider import EmailProvider


def _get_ses_client():
    """Lazy-load boto3 SES client."""
    import boto3

    return boto3.client(
        "ses",
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
    )


class SESProvider(EmailProvider):

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
            client = _get_ses_client()

            if attachments:
                # Attachments require raw MIME via send_raw_email
                return self._send_raw(
                    client, from_email, to_email, subject,
                    body, html_body, attachments, reply_to,
                )

            # No attachments — use the simpler send_email API
            body_payload: Dict[str, Any] = {
                "Text": {"Data": body, "Charset": "UTF-8"},
            }
            if html_body:
                body_payload["Html"] = {"Data": html_body, "Charset": "UTF-8"}

            kwargs: Dict[str, Any] = {
                "Source": from_email,
                "Destination": {"ToAddresses": [to_email]},
                "Message": {
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": body_payload,
                },
            }
            if reply_to:
                kwargs["ReplyToAddresses"] = [reply_to]

            result = client.send_email(**kwargs)
            return {
                "success": True,
                "message_id": result.get("MessageId"),
                "error": None,
            }
        except Exception as exc:
            return {"success": False, "message_id": None, "error": str(exc)}

    def _send_raw(
        self,
        client,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str],
        attachments: List[Tuple[str, bytes, str]],
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build a raw MIME message with attachments and send via SES."""
        msg = MIMEMultipart("mixed")
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        if reply_to:
            msg["Reply-To"] = reply_to

        # Body (alternative: plain + html)
        if html_body:
            alt = MIMEMultipart("alternative")
            alt.attach(MIMEText(body, "plain"))
            alt.attach(MIMEText(html_body, "html"))
            msg.attach(alt)
        else:
            msg.attach(MIMEText(body, "plain"))

        # Attachments
        for filename, file_bytes, mime_type in attachments:
            maintype, subtype = mime_type.split("/", 1)
            part = MIMEBase(maintype, subtype)
            part.set_payload(file_bytes)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(part)

        result = client.send_raw_email(
            Source=from_email,
            Destinations=[to_email],
            RawMessage={"Data": msg.as_string()},
        )
        return {
            "success": True,
            "message_id": result.get("MessageId"),
            "error": None,
        }

    def validate_sender(self, from_email: str) -> Dict[str, Any]:
        try:
            client = _get_ses_client()
            response = client.get_identity_verification_attributes(
                Identities=[from_email]
            )
            attrs = response.get("VerificationAttributes", {}).get(from_email, {})
            status = attrs.get("VerificationStatus")
            if status == "Success":
                return {"verified": True, "detail": "Email verified in SES."}
            return {
                "verified": False,
                "detail": f"SES verification status: {status or 'not found'}. "
                "Verify via POST /send/ses/verify first.",
            }
        except Exception as exc:
            return {"verified": False, "detail": f"SES check failed: {exc}"}

    def provider_name(self) -> str:
        return "ses"
