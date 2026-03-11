"""
Background SQS worker that processes batch email generation jobs.

Runs as a daemon thread — polls SQS, processes one URL at a time
through the existing scrape → generate → send pipeline.
"""

import json
import logging
import threading
import time

from app.services.sqs_client import delete_message, get_queue_url, poll_messages
from app.utils.batch_store import update_batch_result

logger = logging.getLogger(__name__)

_worker_thread: threading.Thread | None = None
_stop_event = threading.Event()


def _process_message(message: dict) -> None:
    """Run the full pipeline for a single URL from an SQS message."""
    body = json.loads(message["Body"])
    url = body["url"]
    job_id = body["job_id"]

    # Mark as processing
    update_batch_result(job_id, url, status="processing")

    try:
        # --- Reuse existing pipeline functions ---
        from app.utils.scraper import scrape_company
        from app.utils.hunter_client import domain_search, company_enrichment, normalize_domain
        from app.utils.company_analyzer import analyze_company, score_contact
        from app.utils.generate import get_openai_response
        from app.utils.resume_store import get_resume
        from app.services.provider_factory import get_provider

        # Resolve resume
        resume_profile = body.get("resume_profile")
        resume_file_bytes = None
        resume_id = body.get("resume_id")
        if resume_id:
            stored = get_resume(resume_id)
            if stored:
                resume_profile = stored["profile"]
                resume_file_bytes = stored.get("file_bytes")

        # 1. Scrape
        scraped_data = scrape_company(url)
        if not isinstance(scraped_data, dict):
            scraped_data = {"url": url, "blocked": True, "error": "Scrape returned no data"}

        # 2. Hunter lookup
        domain = normalize_domain(url)
        company_data = None
        best_contact = None

        if domain and "." in domain:
            search_result = domain_search(company=domain, limit=10)

            if search_result.get("success"):
                data = search_result.get("data") or {}

                org_raw = data.get("organization")
                org = org_raw if isinstance(org_raw, dict) else {}
                org_name = org.get("name") if isinstance(org_raw, dict) else (
                    org_raw if isinstance(org_raw, str) else None
                )

                company_data = {
                    "name": org_name or data.get("organization_name") or domain,
                    "domain": data.get("domain") or domain,
                    "employee_count": org.get("headcount") or data.get("headcount"),
                    "description": org.get("description") or data.get("description"),
                    "industry": org.get("industry") or data.get("industry"),
                }

                if not company_data["employee_count"] or not company_data["description"]:
                    enrichment = company_enrichment(domain)
                    if enrichment.get("success"):
                        enriched = enrichment.get("data") or {}
                        company_data["employee_count"] = company_data["employee_count"] or enriched.get("headcount")
                        company_data["description"] = company_data["description"] or enriched.get("description")
                        company_data["industry"] = company_data["industry"] or enriched.get("industry")

                # Rank contacts
                emails = data.get("emails") or []
                if isinstance(emails, list) and emails:
                    analysis = analyze_company(company_data)
                    ranked = []
                    for contact in emails:
                        if not isinstance(contact, dict):
                            continue
                        title = contact.get("position")
                        role_score = score_contact(
                            title=title, prioritized_roles=analysis["prioritized_roles"]
                        )
                        confidence = contact.get("confidence") or 0
                        ranked.append({
                            "name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip() or "Unknown",
                            "title": title,
                            "email": contact.get("value"),
                            "seniority": contact.get("seniority"),
                            "confidence": confidence,
                            "role_score": role_score,
                        })

                    ranked.sort(key=lambda c: (c["role_score"], c["confidence"]), reverse=True)
                    if ranked:
                        best_contact = ranked[0]

        # 3. Generate email
        email_result = get_openai_response(
            scraped_data=scraped_data,
            company_data=company_data,
            resume_data=resume_profile,
            contact_data=best_contact,
            mode=body.get("mode", "template"),
            template=body.get("template"),
            subject_template=body.get("subject_template"),
            linkedin_url=body.get("linkedin_url"),
            github_url=body.get("github_url"),
            smooth_grammar=body.get("smooth_grammar", True),
        )

        # 4. Build HTML email and attachments
        from app.utils.html_builder import (
            markdown_to_html,
            wrap_html_email,
            build_plain_text_fallback,
        )

        linkedin = email_result.get("linkedin_url", "")
        github = email_result.get("github_url", "")
        sender_name = (resume_profile or {}).get("name", "")

        body_html = markdown_to_html(email_result["body"])
        html_body = wrap_html_email(body_html, linkedin, github, sender_name)
        plain_body = build_plain_text_fallback(email_result["body"], linkedin, github)

        # Build attachments list
        attachments = []
        if resume_file_bytes:
            safe_name = sender_name.replace(" ", "_") if sender_name else "Resume"
            attachments.append((f"{safe_name}_Resume.pdf", resume_file_bytes, "application/pdf"))

        # 5. Send or schedule
        from_email = body["from_email"]
        to_email = best_contact["email"] if best_contact else None

        result_data = {
            "email": {
                "subject": email_result["subject"],
                "body": email_result["body"],
                "html_body": html_body,
                "to_email": to_email,
                "to_name": best_contact["name"] if best_contact else None,
            },
            "contact": best_contact,
            "company": company_data,
        }

        if not to_email:
            update_batch_result(job_id, url, status="failed", result=result_data, error="No contact email found")
            return

        provider = get_provider(from_email)
        send_at = body.get("send_at")

        if send_at:
            # Schedule for later — create Gmail draft + EventBridge schedule
            from datetime import datetime, timezone
            from app.services.scheduler import create_schedule

            draft_result = provider.create_draft(
                from_email=from_email,
                to_email=to_email,
                subject=email_result["subject"],
                body=plain_body,
                html_body=html_body,
                attachments=attachments or None,
            )

            if not draft_result["success"]:
                update_batch_result(job_id, url, status="failed", result=result_data, error=f"Draft creation failed: {draft_result['error']}")
                return

            send_time = datetime.fromisoformat(send_at)
            if send_time.tzinfo is None:
                send_time = send_time.replace(tzinfo=timezone.utc)

            create_schedule(
                draft_id=draft_result["draft_id"],
                send_at=send_time,
                from_email=from_email,
            )
            result_data["draft_id"] = draft_result["draft_id"]
            update_batch_result(job_id, url, status="scheduled", result=result_data)
        else:
            # Send instantly
            send_result = provider.send(
                from_email=from_email,
                to_email=to_email,
                subject=email_result["subject"],
                body=plain_body,
                html_body=html_body,
                attachments=attachments or None,
            )

            if send_result["success"]:
                result_data["message_id"] = send_result["message_id"]
                update_batch_result(job_id, url, status="sent", result=result_data)
            else:
                update_batch_result(job_id, url, status="failed", result=result_data, error=send_result["error"])

    except Exception as exc:
        logger.exception("Batch worker error processing %s", url)
        update_batch_result(job_id, url, status="failed", error=str(exc))


def _worker_loop() -> None:
    """Main worker loop — polls SQS and processes messages."""
    queue_url = get_queue_url()
    if not queue_url:
        logger.warning("SQS_QUEUE_URL not set — batch worker idle")
        return

    logger.info("Batch worker started, polling %s", queue_url)

    while not _stop_event.is_set():
        try:
            messages = poll_messages(queue_url, max_messages=1, wait_time=5)
            for msg in messages:
                _process_message(msg)
                delete_message(queue_url, msg["ReceiptHandle"])
        except Exception:
            logger.exception("Batch worker poll error")
            time.sleep(2)


def start_worker() -> None:
    """Start the background SQS worker thread."""
    global _worker_thread
    if _worker_thread and _worker_thread.is_alive():
        return

    _stop_event.clear()
    _worker_thread = threading.Thread(target=_worker_loop, daemon=True)
    _worker_thread.start()


def stop_worker() -> None:
    """Signal the worker to stop."""
    _stop_event.set()
