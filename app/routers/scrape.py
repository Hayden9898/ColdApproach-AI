from fastapi import APIRouter, HTTPException

from app.models.schemas import GenerateEmailRequest
from app.utils.scraper import scrape_company
from app.utils.generate import get_openai_response
from app.utils.html_builder import markdown_to_html, wrap_html_email, build_plain_text_fallback
from app.utils.hunter_client import domain_search, company_enrichment, normalize_domain
from app.utils.company_analyzer import analyze_company, score_contact
from app.utils.resume_store import get_resume

router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.get("/")
def scrape_url(url: str):
    """
    Pure company webpage scrape endpoint.
    No OpenAI call is made here.
    """
    result = scrape_company(url)
    if not isinstance(result, dict):
        raise HTTPException(status_code=500, detail="Failed to scrape company.")

    if result.get("error"):
        raise HTTPException(status_code=500, detail=f"Scrape failed: {result['error']}")

    return {
        "success": True,
        "company_data": result,
        "note": "Scrape-only response (no LLM generation).",
    }


@router.post("/generate")
def generate_email(request: GenerateEmailRequest):
    """
    Full pipeline: scrape website + lookup contacts via Hunter + generate personalized email.
    Supports two modes:
        - "template" (default): fill user-provided template with context data
        - "ml": fully GPT-generated email (not yet available)
    Returns an SES-ready response with subject, body, and recipient info.
    """
    # Mode guard — ML is locked for now
    if request.mode == "ml":
        raise HTTPException(status_code=400, detail="ML mode is not yet available.")

    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required.")

    if request.mode == "template" and not request.template:
        raise HTTPException(status_code=400, detail="Template is required when using template mode.")

    # Resolve resume_id → resume_profile if provided
    resume_profile = request.resume_profile
    if request.resume_id:
        stored = get_resume(request.resume_id)
        if not stored:
            raise HTTPException(status_code=404, detail="Resume not found. Upload again via /resume/upload.")
        resume_profile = stored["profile"]

    # 1. Scrape the company website for content
    scraped_data = scrape_company(url)
    if not isinstance(scraped_data, dict):
        scraped_data = {"url": url, "blocked": True, "error": "Scrape returned no data"}

    # 2. Look up contacts + company metadata via Hunter
    domain = normalize_domain(url)
    company_data = None
    best_contact = None

    if domain and "." in domain:
        search_result = domain_search(company=domain, limit=10)

        if search_result.get("success"):
            data = search_result.get("data") or {}

            # Extract company info from Hunter
            org_raw = data.get("organization")
            org = org_raw if isinstance(org_raw, dict) else {}
            org_name = org.get("name") if isinstance(org_raw, dict) else (org_raw if isinstance(org_raw, str) else None)

            company_data = {
                "name": org_name or data.get("organization_name") or domain,
                "domain": data.get("domain") or domain,
                "employee_count": org.get("headcount") or data.get("headcount"),
                "description": org.get("description") or data.get("description"),
                "industry": org.get("industry") or data.get("industry"),
                "website_url": org.get("website") or data.get("website"),
                "city": org.get("city") or data.get("city"),
                "state": org.get("state") or data.get("state"),
                "country": org.get("country") or data.get("country"),
            }

            # Enrich if missing size or description
            if not company_data["employee_count"] or not company_data["description"]:
                enrichment = company_enrichment(domain)
                if enrichment.get("success"):
                    enriched = enrichment.get("data") or {}
                    company_data["employee_count"] = company_data["employee_count"] or enriched.get("headcount")
                    company_data["description"] = company_data["description"] or enriched.get("description")
                    company_data["industry"] = company_data["industry"] or enriched.get("industry")

            # Rank contacts and pick best fit
            emails = data.get("emails") or []
            if isinstance(emails, list) and emails:
                analysis = analyze_company(company_data)
                ranked = []
                for contact in emails:
                    if not isinstance(contact, dict):
                        continue
                    title = contact.get("position")
                    role_score = score_contact(title=title, prioritized_roles=analysis["prioritized_roles"])
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

    # 3. Generate the email
    email_result = get_openai_response(
        scraped_data=scraped_data,
        company_data=company_data,
        resume_data=resume_profile,
        contact_data=best_contact,
        mode=request.mode,
        template=request.template,
        subject_template=request.subject_template,
        linkedin_url=request.linkedin_url,
        github_url=request.github_url,
    )

    # 4. Build HTML version for preview
    linkedin = email_result.get("linkedin_url", "")
    github = email_result.get("github_url", "")
    sender_name = (resume_profile or {}).get("name", "")

    body_html = markdown_to_html(email_result["body"])
    html_body = wrap_html_email(body_html, linkedin, github, sender_name)

    # 5. Build SES-ready response
    response = {
        "email": {
            "subject": email_result["subject"],
            "body": email_result["body"],
            "html_body": html_body,
            "to_email": best_contact["email"] if best_contact else None,
            "to_name": best_contact["name"] if best_contact else None,
        },
        "contact": {
            "name": best_contact["name"],
            "title": best_contact.get("title"),
            "email": best_contact["email"],
            "seniority": best_contact.get("seniority"),
            "confidence": best_contact.get("confidence"),
        } if best_contact else None,
        "company": {
            "name": company_data.get("name"),
            "domain": company_data.get("domain"),
            "industry": company_data.get("industry"),
            "description": company_data.get("description"),
            "employee_count": company_data.get("employee_count"),
        } if company_data else None,
    }

    return response
