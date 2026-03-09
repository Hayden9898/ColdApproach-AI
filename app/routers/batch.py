"""
Batch processing endpoints.
Submit multiple URLs for async email generation and sending via SQS.
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import BATCH_LIMIT, BatchSubmitRequest, BatchStatusResponse
from app.services.provider_factory import get_provider
from app.services.sqs_client import enqueue_message, get_queue_url
from app.utils.batch_store import get_batch, save_batch

router = APIRouter(prefix="/batch", tags=["batch"])


@router.post("/submit")
def submit_batch(request: BatchSubmitRequest):
    """
    Submit a batch of URLs for async processing.

    Each URL is queued to SQS and processed one at a time:
    scrape → Hunter lookup → generate email → send (or schedule).

    Returns a job_id immediately — poll /batch/{job_id}/status for progress.
    """
    urls = [u.strip() for u in request.urls if u.strip()]

    if not urls:
        raise HTTPException(status_code=400, detail="At least one URL is required.")

    if len(urls) > BATCH_LIMIT:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {BATCH_LIMIT} URLs per batch. You submitted {len(urls)}.",
        )

    # Validate sender is authorized
    provider = get_provider(request.from_email)
    validation = provider.validate_sender(request.from_email)
    if not validation["verified"]:
        raise HTTPException(status_code=403, detail=validation["detail"])

    queue_url = get_queue_url()
    if not queue_url:
        raise HTTPException(status_code=500, detail="SQS_QUEUE_URL not configured.")

    # Create batch job
    job_id = save_batch(
        urls=urls,
        from_email=request.from_email,
        send_at=request.send_at,
    )

    # Enqueue each URL as a separate SQS message
    for url in urls:
        enqueue_message(queue_url, {
            "url": url,
            "job_id": job_id,
            "from_email": request.from_email,
            "resume_id": request.resume_id,
            "resume_profile": request.resume_profile,
            "mode": request.mode,
            "template": request.template,
            "subject_template": request.subject_template,
            "linkedin_url": request.linkedin_url,
            "github_url": request.github_url,
            "smooth_grammar": request.smooth_grammar,
            "send_at": request.send_at.isoformat() if request.send_at else None,
        })

    return {
        "success": True,
        "job_id": job_id,
        "status": "queued",
        "total": len(urls),
    }


@router.get("/{job_id}/status", response_model=BatchStatusResponse)
def batch_status(job_id: str):
    """Poll batch job progress and per-URL results."""
    job = get_batch(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found.")

    return BatchStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        total=job["total"],
        completed=job["completed"],
        failed=job["failed"],
        results=job["results"],
    )
