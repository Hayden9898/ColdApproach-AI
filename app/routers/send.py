"""
Email sending endpoints.
Auto-detects provider (Gmail/SES) from sender email domain.
Supports instant and scheduled sends.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.models.schemas import SendEmailRequest, SendEmailResponse, SESVerifyRequest
from app.services.provider_factory import get_provider
from app.utils.email_store import get_email, save_email

router = APIRouter(prefix="/send", tags=["send"])


@router.post("/email", response_model=SendEmailResponse)
def send_email(request: SendEmailRequest):
    """
    Send an email immediately or schedule it for later.

    Auto-detection:
        @gmail.com sender -> Gmail API (requires prior OAuth via /auth/gmail/login)
        Custom domain      -> Amazon SES (requires email verification)

    If send_at is provided (UTC), schedules via EventBridge Scheduler.
    Otherwise sends immediately.
    """
    provider = get_provider(request.from_email)

    # Validate sender authorization
    validation = provider.validate_sender(request.from_email)
    if not validation["verified"]:
        raise HTTPException(status_code=403, detail=validation["detail"])

    # --- Scheduled send ---
    if request.send_at:
        send_time = request.send_at
        if send_time.tzinfo is None:
            send_time = send_time.replace(tzinfo=timezone.utc)

        if send_time <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="send_at must be in the future.")

        # Store payload for Lambda retrieval
        email_id = save_email({
            "from_email": request.from_email,
            "to_email": request.to_email,
            "subject": request.subject,
            "body": request.body,
            "reply_to": request.reply_to,
        })

        from app.services.scheduler import create_schedule

        schedule_result = create_schedule(
            email_id=email_id,
            send_at=send_time,
            provider_name=provider.provider_name(),
            from_email=request.from_email,
        )

        if not schedule_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Scheduling failed: {schedule_result['error']}",
            )

        return SendEmailResponse(
            success=True,
            provider=provider.provider_name(),
            scheduled=True,
            scheduled_at=send_time.isoformat(),
            email_id=email_id,
        )

    # --- Instant send ---
    result = provider.send(
        from_email=request.from_email,
        to_email=request.to_email,
        subject=request.subject,
        body=request.body,
        reply_to=request.reply_to,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=f"Send failed: {result['error']}")

    return SendEmailResponse(
        success=True,
        provider=provider.provider_name(),
        message_id=result["message_id"],
    )


@router.post("/ses/verify")
def verify_ses_email(request: SESVerifyRequest):
    """Trigger SES email verification for a custom domain sender."""
    try:
        import boto3
        import os

        client = boto3.client(
            "ses", region_name=os.environ.get("AWS_REGION", "us-east-1")
        )
        client.verify_email_identity(EmailAddress=request.email)
        return {
            "success": True,
            "email": request.email,
            "message": "Verification email sent. Check your inbox and click the link.",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"SES verification failed: {exc}"
        )


@router.get("/ses/status")
def ses_verification_status(email: str):
    """Check SES verification status for an email address."""
    from app.services.ses_provider import SESProvider

    provider = SESProvider()
    result = provider.validate_sender(email)
    return {"email": email, **result}


@router.get("/scheduled/{email_id}")
def get_scheduled_email(email_id: str):
    """Retrieve a stored scheduled email payload (used by Lambda)."""
    email_data = get_email(email_id)
    if not email_data:
        raise HTTPException(status_code=404, detail="Scheduled email not found.")
    return {"success": True, "email": email_data}
