"""
In-memory OAuth token store.

Holds access/refresh tokens keyed by user email so the send endpoint
can retrieve them. Memory is freed when the FastAPI process stops.
"""

from typing import Any, Dict, Optional

_store: Dict[str, Dict[str, Any]] = {}


def save_token(email: str, token_data: dict) -> None:
    """Store OAuth token data keyed by the user's email."""
    _store[email.lower()] = token_data


def get_token(email: str) -> Optional[Dict[str, Any]]:
    """Retrieve token data by email, or None if not found."""
    return _store.get(email.lower())


def delete_token(email: str) -> None:
    """Remove a token from the store."""
    _store.pop(email.lower(), None)
