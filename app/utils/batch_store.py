"""
In-memory batch job store.

Tracks batch processing jobs — each job contains multiple URLs
with their individual processing status and results.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

_store: Dict[str, Dict[str, Any]] = {}


def save_batch(
    urls: list,
    from_email: str,
    send_at: Optional[datetime] = None,
) -> str:
    """Create a new batch job and return its ID."""
    job_id = str(uuid.uuid4())
    _store[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "from_email": from_email,
        "send_at": send_at.isoformat() if send_at else None,
        "total": len(urls),
        "completed": 0,
        "failed": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "results": {url: {"status": "queued"} for url in urls},
    }
    return job_id


def get_batch(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a batch job by ID."""
    return _store.get(job_id)


def update_batch_result(
    job_id: str,
    url: str,
    status: str,
    result: Optional[dict] = None,
    error: Optional[str] = None,
) -> None:
    """Update a single URL's result within a batch job."""
    job = _store.get(job_id)
    if not job:
        return

    job["results"][url] = {"status": status}
    if result:
        job["results"][url].update(result)
    if error:
        job["results"][url]["error"] = error

    if status == "sent" or status == "scheduled":
        job["completed"] += 1
    elif status == "failed":
        job["failed"] += 1

    # Update overall job status
    total = job["total"]
    done = job["completed"] + job["failed"]
    if done >= total:
        job["status"] = "completed"
    else:
        job["status"] = "processing"
