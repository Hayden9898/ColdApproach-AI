"""
Apollo API client - Fetch company data and search for people.
"""
import os
import requests
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load .env file to ensure environment variables are available
load_dotenv()

APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY")
APOLLO_BASE_URL = "https://api.apollo.io/api/v1"


def extract_domain_from_url(url: str) -> str:
    """
    Extract domain from a URL.
    
    Examples:
        "https://www.stilla.ai/about" -> "stilla.ai"
        "http://stilla.ai" -> "stilla.ai"
        "stilla.ai" -> "stilla.ai"
    """
    # Remove protocol
    if "://" in url:
        url = url.split("://")[1]
    
    # Remove path
    if "/" in url:
        url = url.split("/")[0]
    
    # Remove www.
    if url.startswith("www."):
        url = url[4:]
    
    return url.lower().strip()


def get_apollo_headers() -> Dict[str, str]:
    """Get headers for Apollo API requests."""
    if not APOLLO_API_KEY:
        raise RuntimeError(
            "APOLLO_API_KEY environment variable not set. "
            "Get your API key at: https://app.apollo.io/#/settings/integrations/api"
        )
    return {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_API_KEY
    }


def search_company_by_domain(domain: str) -> Dict[str, Any]:
    """
    Search Apollo for company data by domain.
    Returns employee count and company info.
    
    Args:
        domain: Company domain (e.g., "stilla.ai")
    
    Returns:
        Company data including employee_count
    """
    if not APOLLO_API_KEY:
        return {
            "success": False,
            "error": "APOLLO_API_KEY not configured. Set it in your .env file.",
            "company": None
        }
    
    url = f"{APOLLO_BASE_URL}/organizations/search"
    
    headers = get_apollo_headers()
    
    payload = {
        "q_organization_domains_list": [domain],
        "page": 1,
        "per_page": 1,  # We only need the first match
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        organizations = data.get("organizations", [])
        
        if not organizations:
            return {
                "success": False,
                "error": "Company not found in Apollo database",
                "company": None
            }
        
        org = organizations[0]
        
        return {
            "success": True,
            "company": {
                "id": org.get("id"),
                "name": org.get("name"),
                "website_url": org.get("website_url"),
                "employee_count": org.get("estimated_num_employees"),  # Key field for size categorization
                "industry": org.get("industry"),
                "keywords": org.get("keywords", []),
                "linkedin_url": org.get("linkedin_url"),
                "city": org.get("city"),
                "state": org.get("state"),
                "country": org.get("country"),
            }
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "company": None
        }


def search_people_minimal(
    domain: str,
    organization_id: Optional[str] = None,
    job_titles: Optional[List[str]] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search Apollo for people using FREE endpoint: /mixed_people/organization_top_people.
    
    Args:
        domain: Company domain
        organization_id: Apollo organization ID (optional, can get from company search)
        job_titles: Optional list of job titles to filter (may not be supported by this endpoint)
        limit: Maximum number of results (default: 10)
    
    Returns:
        Dictionary with contacts (name, title, email)
    """
    if not APOLLO_API_KEY:
        return {
            "success": False,
            "error": "APOLLO_API_KEY not configured",
            "contacts": []
        }
    
    # Use FREE endpoint: /mixed_people/organization_top_people
    url = f"{APOLLO_BASE_URL}/mixed_people/organization_top_people"
    
    headers = get_apollo_headers()
    
    # This endpoint needs organization_id (get from company search)
    payload = {}
    if organization_id:
        payload["organization_id"] = organization_id
    else:
        # If no organization_id, try domain (may not work, but worth trying)
        payload["q_organization_domains"] = [domain]
    
    # Note: organization_top_people returns "top people" - may not support job_titles filter
    # But we'll filter client-side if needed
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract contacts from response
        # Response format may vary - check for people/contacts array
        contacts_data = (
            data.get("people", []) or 
            data.get("contacts", []) or 
            data.get("organization_top_people", []) or
            data.get("top_people", []) or
            []
        )
        
        contacts = []
        for person in contacts_data[:limit]:
            # Filter by job titles if provided (client-side filtering)
            title = person.get("title", "").lower()
            if job_titles:
                # Check if person's title matches any of our target roles
                matches = any(
                    role.lower() in title or title in role.lower()
                    for role in job_titles
                )
                if not matches:
                    continue  # Skip if doesn't match target roles
            
            contacts.append({
                "name": person.get("name") or f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                "title": person.get("title"),
                "email": person.get("email"),  # May be None
                "apollo_id": person.get("id"),
                "linkedin_url": person.get("linkedin_url"),
            })
        
        return {
            "success": True,
            "count": len(contacts),
            "contacts": contacts,
            "debug_info": {
                "raw_response_keys": list(data.keys()),
                "total_people_in_response": len(contacts_data),
                "after_filtering": len(contacts)
            } if len(contacts_data) > 0 else None
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "contacts": [],
            "debug_info": {
                "status_code": response.status_code if 'response' in locals() else None,
                "response_text": response.text[:500] if 'response' in locals() else None
            }
        }
