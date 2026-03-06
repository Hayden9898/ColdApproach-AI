"""
Lambda handler invoked by EventBridge Scheduler at the scheduled send time.

Retrieves the stored email payload from the FastAPI API and sends it
by calling the /send/email endpoint (without send_at, so it sends instantly).
"""

import json
import os
import urllib.request

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def handler(event, context):
    email_id = event.get("email_id")
    if not email_id:
        return {"statusCode": 400, "body": "Missing email_id"}

    # Fetch stored email payload
    get_url = f"{API_BASE_URL}/send/scheduled/{email_id}"
    req = urllib.request.Request(get_url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = json.loads(resp.read())

    if not payload.get("success"):
        return {"statusCode": 404, "body": f"Email {email_id} not found"}

    email_data = payload["email"]

    # Send immediately (no send_at)
    send_url = f"{API_BASE_URL}/send/email"
    send_body = json.dumps({
        "from_email": email_data["from_email"],
        "to_email": email_data["to_email"],
        "subject": email_data["subject"],
        "body": email_data["body"],
        "reply_to": email_data.get("reply_to"),
    }).encode()

    send_req = urllib.request.Request(
        send_url,
        data=send_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(send_req, timeout=30) as resp:
        result = json.loads(resp.read())

    return {"statusCode": 200, "body": json.dumps(result)}
