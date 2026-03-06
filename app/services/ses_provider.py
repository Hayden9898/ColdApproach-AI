"""
Amazon SES email provider for custom domain senders.
Requires the sender email (or domain) to be verified in SES.
"""

import os
from typing import Any, Dict, Optional

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
    ) -> Dict[str, Any]:
        try:
            client = _get_ses_client()
            kwargs: Dict[str, Any] = {
                "Source": from_email,
                "Destination": {"ToAddresses": [to_email]},
                "Message": {
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
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
