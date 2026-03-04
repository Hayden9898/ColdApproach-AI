"""
In-memory resume store.

Holds uploaded resume PDF bytes and parsed profile keyed by UUID so other
endpoints can retrieve them. Memory is freed when the FastAPI process stops.
"""

import uuid
from typing import Any, Dict, Optional

_store: Dict[str, Dict[str, Any]] = {}


def save_resume(file_bytes: bytes, profile: dict) -> str:
    """Store PDF bytes + parsed profile and return a unique resume_id."""
    resume_id = str(uuid.uuid4())
    _store[resume_id] = {"file_bytes": file_bytes, "profile": profile}
    return resume_id


def get_resume(resume_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve stored data by resume_id, or None if not found.
    Returns {"file_bytes": bytes, "profile": dict}."""
    return _store.get(resume_id)


def delete_resume(resume_id: str) -> None:
    """Remove a resume from the store."""
    _store.pop(resume_id, None)
