"""
In-memory store for email payloads awaiting scheduled delivery.

Keyed by UUID. Lambda retrieves the payload at send time.
"""

import uuid
from typing import Any, Dict, Optional

_store: Dict[str, Dict[str, Any]] = {}


def save_email(payload: dict) -> str:
    """Store email payload and return a unique email_id."""
    email_id = str(uuid.uuid4())
    _store[email_id] = payload
    return email_id


def get_email(email_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve stored email by ID."""
    return _store.get(email_id)


def delete_email(email_id: str) -> None:
    """Remove email from store (after successful send)."""
    _store.pop(email_id, None)
