from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.utils.scraper import scrape_company
from app.utils.generate import get_openai_response
from app.utils.hunter_client import domain_search, company_enrichment, normalize_domain
from app.utils.company_analyzer import analyze_company, score_contact

router = APIRouter(prefix="/scrape", tags=["scrape"])


class GenerateEmailRequest(BaseModel):
    url: str
    resume_profile: Optional[dict] = None


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
    Returns an SES-ready response with subject, body, and recipient info.
    """
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required.")

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
        resume_data=request.resume_profile,
        contact_data=best_contact,
    )

    # 4. Build SES-ready response
    response = {
        "email": {
            "subject": email_result["subject"],
            "body": email_result["body"],
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
