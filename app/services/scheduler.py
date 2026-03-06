"""
AWS EventBridge Scheduler integration for delayed email sends.
Creates a one-time schedule that invokes a Lambda at the specified time.
The schedule auto-deletes after execution.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict


def _get_scheduler_client():
    """Lazy-load boto3 EventBridge Scheduler client."""
    import boto3

    return boto3.client(
        "scheduler",
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
    )


def create_schedule(
    email_id: str,
    send_at: datetime,
    provider_name: str,
    from_email: str,
) -> Dict[str, Any]:
    """
    Create a one-time EventBridge schedule to invoke the send Lambda.

    Returns {"success": bool, "schedule_name": str|None, "error": str|None}
    """
    lambda_arn = os.environ.get("SEND_EMAIL_LAMBDA_ARN", "")
    scheduler_role_arn = os.environ.get("SCHEDULER_ROLE_ARN", "")

    if not lambda_arn or not scheduler_role_arn:
        return {
            "success": False,
            "schedule_name": None,
            "error": "SEND_EMAIL_LAMBDA_ARN or SCHEDULER_ROLE_ARN not configured.",
        }

    schedule_name = f"coldreach-send-{email_id}"
    schedule_expression = f"at({send_at.strftime('%Y-%m-%dT%H:%M:%S')})"

    try:
        client = _get_scheduler_client()
        client.create_schedule(
            Name=schedule_name,
            ScheduleExpression=schedule_expression,
            ScheduleExpressionTimezone="UTC",
            FlexibleTimeWindow={"Mode": "OFF"},
            Target={
                "Arn": lambda_arn,
                "RoleArn": scheduler_role_arn,
                "Input": json.dumps({
                    "email_id": email_id,
                    "provider": provider_name,
                    "from_email": from_email,
                }),
            },
            ActionAfterCompletion="DELETE",
        )
        return {"success": True, "schedule_name": schedule_name, "error": None}
    except Exception as exc:
        return {"success": False, "schedule_name": None, "error": str(exc)}


def delete_schedule(schedule_name: str) -> None:
    """Cancel a scheduled send."""
    try:
        client = _get_scheduler_client()
        client.delete_schedule(Name=schedule_name)
    except Exception:
        pass  # Schedule may have already fired or been deleted
