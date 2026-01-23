"""
Apollo pipeline: Fetch company data first, then search for people.
"""
from fastapi import APIRouter, HTTPException
from app.utils.apollo_client import (
    search_company_by_domain,
    search_people_minimal,
    extract_domain_from_url
)
from app.utils.company_analyzer import analyze_company_from_apollo

router = APIRouter(prefix="/company", tags=["company"])


@router.get("/find")
def find_contacts(company_url: str, limit: int = 10):
    """
    Apollo pipeline: Fetch company data first, then search for people.
    
    Process:
    1. Extract domain from company URL
    2. Fetch company data from Apollo (including employee count)
    3. Categorize company size: 1-30 (small), 30-100 (medium), 100+ (large)
    4. Get prioritized role array based on size
    5. Search for people with those roles
    
    Args:
        company_url: Company website URL (e.g., "https://stilla.ai")
        limit: Maximum number of contacts to return (default: 10)
    
    Returns:
        Company data, size category, prioritized roles, and contacts
    """
    # Step 1: Extract domain
    domain = extract_domain_from_url(company_url)
    
    # Step 2: Fetch company data from Apollo DB
    company_result = search_company_by_domain(domain)
    
    if not company_result.get("success"):
        raise HTTPException(
            status_code=404,
            detail=f"Company not found in Apollo: {company_result.get('error', 'Unknown error')}"
        )
    
    company_data = company_result["company"]
    
    # Step 3: Analyze company and get prioritized roles
    analysis = analyze_company_from_apollo(company_data)
    
    # Step 4: Search for people
    # COMMENTED OUT: /mixed_people/organization_top_people endpoint returns 404 (doesn't exist)
    # Will enable when upgrading to paid plan with /mixed_people/api_search
    # 
    # organization_id = company_data.get("id")
    # people_result = search_people_minimal(
    #     domain=domain,
    #     organization_id=organization_id,
    #     job_titles=analysis["prioritized_roles"],
    #     limit=limit
    # )
    # 
    # contacts = []
    # best_contact = None
    # if people_result.get("success"):
    #     contacts = people_result.get("contacts", [])
    #     # Pick best contact logic...
    
    # For now - return empty contacts (company data works perfectly!)
    # People search will be enabled after upgrading to paid plan
    contacts = []
    best_contact = None
    
    return {
        "company": {
            "name": company_data.get("name"),
            "domain": domain,
            "employee_count": company_data.get("employee_count"),  # Number of employees
            "size_category": analysis["size_category"],
            "website_url": company_data.get("website_url"),
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
            "prioritized_roles_searched": analysis["prioritized_roles"],
        },
        "contacts_found": len(contacts),
        "best_contact": best_contact,  # The best contact selected (null for now)
        "all_contacts": [
            {
                "name": c["name"],
                "title": c["title"],
                "email": c.get("email"),  # May be None - requires enrichment
                "linkedin_url": c.get("linkedin_url")
            }
            for c in contacts
        ],
        "note": "People search disabled - /mixed_people/organization_top_people endpoint returns 404. Company data fetching works perfectly! Enable people search after upgrading to paid plan with /mixed_people/api_search."
    }
