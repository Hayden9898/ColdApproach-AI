"""
Hunter pipeline: fetch contact candidates, rank by role fit, and return best candidate.
"""
from fastapi import APIRouter, HTTPException
from app.utils.company_analyzer import analyze_company, role_priority_config, score_contact
from app.utils.hunter_client import company_enrichment, domain_search, normalize_domain

router = APIRouter(prefix="/company", tags=["company"])


@router.get("/find")
def find_contacts(company: str, limit: int = 10):
    """
    Hunter pipeline:
    1. Search top contacts by company name or domain
    2. Return up to 10 candidates with roles
    3. Score role-fit and choose best candidate
    4. Return all fetched contacts and selected best candidate
    """
    company_input = company.strip()
    if not company_input:
        raise HTTPException(status_code=400, detail="`company` is required and cannot be empty.")

    if limit < 1 or limit > 10:
        raise HTTPException(status_code=400, detail="`limit` must be between 1 and 10.")

    # Guard malformed URL/domain inputs before spending Hunter credits.
    looks_like_url_or_domain = any(x in company_input for x in ["://", "/", "."]) or company_input.startswith("www.")
    if looks_like_url_or_domain:
        domain_candidate = normalize_domain(company_input)
        if not domain_candidate or "." not in domain_candidate:
            raise HTTPException(
                status_code=400,
                detail="Invalid company URL/domain. Example valid input: https://acme.com or acme.com",
            )

    normalized_limit = limit

    search_result = domain_search(company=company_input, limit=normalized_limit)
    if not search_result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=f"Company lookup failed in Hunter: {search_result.get('error', 'Unknown error')}",
        )

    data_raw = search_result.get("data") or {}
    data = data_raw if isinstance(data_raw, dict) else {}

    org_raw = data.get("organization")
    if isinstance(org_raw, dict):
        org = org_raw
        org_name = org.get("name")
    elif isinstance(org_raw, str):
        org = {}
        org_name = org_raw
    else:
        org = {}
        org_name = None

    emails_raw = data.get("emails") or []
    emails = emails_raw if isinstance(emails_raw, list) else []
    emails = emails[:normalized_limit]

    company_data = {
        "name": org_name or data.get("organization_name") or company,
        "domain": data.get("domain"),
        "employee_count": org.get("headcount") or data.get("headcount"),
        "description": org.get("description") or data.get("description"),
        "industry": org.get("industry") or data.get("industry"),
        "website_url": org.get("website") or data.get("website"),
        "city": org.get("city") or data.get("city"),
        "state": org.get("state") or data.get("state"),
        "country": org.get("country") or data.get("country"),
    }

    # Domain Search usually includes org metadata, but enrich when size/description is missing.
    if company_data["domain"] and (not company_data["employee_count"] or not company_data["description"]):
        enrichment_result = company_enrichment(company_data["domain"])
        if enrichment_result.get("success"):
            enriched = enrichment_result.get("data") or {}
            company_data["employee_count"] = company_data["employee_count"] or enriched.get("headcount")
            company_data["description"] = company_data["description"] or enriched.get("description")
            company_data["industry"] = company_data["industry"] or enriched.get("industry")
            company_data["website_url"] = company_data["website_url"] or enriched.get("website")
            company_data["city"] = company_data["city"] or enriched.get("city")
            company_data["state"] = company_data["state"] or enriched.get("state")
            company_data["country"] = company_data["country"] or enriched.get("country")

    analysis = analyze_company(company_data)

    ranked_candidates = []
    for contact in emails:
        if not isinstance(contact, dict):
            continue
        title = contact.get("position")
        role_score = score_contact(title=title, prioritized_roles=analysis["prioritized_roles"])
        confidence = contact.get("confidence") or 0
        ranked_candidates.append(
            {
                "first_name": contact.get("first_name"),
                "last_name": contact.get("last_name"),
                "name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip() or "Unknown",
                "title": title,
                "linkedin_url": contact.get("linkedin"),
                "department": contact.get("department"),
                "seniority": contact.get("seniority"),
                "confidence": confidence,
                "email": contact.get("value"),
                "role_score": role_score,
            }
        )

    ranked_candidates.sort(key=lambda c: (c["role_score"], c["confidence"]), reverse=True)

    best_contact = ranked_candidates[0] if ranked_candidates else None

    all_contacts = [
        {
            "name": c["name"],
            "title": c["title"],
            "linkedin_url": c["linkedin_url"],
            "seniority": c["seniority"],
            "confidence": c["confidence"],
            "email": c["email"],
            "selected_best_fit": bool(best_contact and c["name"] == best_contact["name"] and c["email"] == best_contact["email"]),
        }
        for c in ranked_candidates
    ]

    revealed_best = None
    if best_contact:
        revealed_best = {
            "name": best_contact["name"],
            "title": best_contact["title"],
            "linkedin_url": best_contact["linkedin_url"],
            "seniority": best_contact["seniority"],
            "confidence": best_contact["confidence"],
            "email": best_contact["email"],  # Reveal email only for best fit
        }

    return {
        "company": {
            "name": company_data.get("name"),
            "domain": company_data.get("domain"),
            "employee_count": company_data.get("employee_count"),
            "size_category": analysis["size_category"],
            "website_url": company_data.get("website_url"),
            "description": company_data.get("description"),
            "industry": company_data.get("industry"),
            "location": {
                "city": company_data.get("city"),
                "state": company_data.get("state"),
                "country": company_data.get("country"),
            }
        },
        "strategy": {
            "category": analysis["size_category"],
            "description": analysis["strategy"],
            "prioritized_roles": analysis["prioritized_roles"],
            "role_priority_config": role_priority_config(),
        },
        "contacts_found": len(ranked_candidates),
        "best_contact": revealed_best,
        "all_contacts": all_contacts,
        "note": "Returns up to 10 contacts, role-ranked by company size strategy.",
    }
