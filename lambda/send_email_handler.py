"""
Lambda handler invoked by EventBridge Scheduler at the scheduled send time.

Sends a Gmail draft by calling the /send/draft endpoint on the FastAPI API.
"""

import json
import os
import urllib.request

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
API_KEY = os.environ.get("API_KEY", "")


def handler(event, context):
    draft_id = event.get("draft_id")
    from_email = event.get("from_email")

    if not draft_id or not from_email:
        return {"statusCode": 400, "body": "Missing draft_id or from_email"}

    send_url = f"{API_BASE_URL}/send/draft"
    send_body = json.dumps({
        "draft_id": draft_id,
        "from_email": from_email,
    }).encode()

    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    send_req = urllib.request.Request(
        send_url,
        data=send_body,
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(send_req, timeout=30) as resp:
        result = json.loads(resp.read())

    return {"statusCode": 200, "body": json.dumps(result)}
