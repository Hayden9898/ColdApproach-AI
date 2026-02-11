"""
Hunter API client - find company contacts by domain/company.
"""
import os
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY")
HUNTER_BASE_URL = "https://api.hunter.io/v2"


def normalize_domain(value: str) -> str:
    """
    Normalize input into a bare domain when possible.
    """
    raw = value.strip()
    if not raw:
        return ""

    if "://" not in raw:
        raw = f"https://{raw}"

    parsed = urlparse(raw)
    host = parsed.netloc or parsed.path
    host = host.lower().strip()
    if host.startswith("www."):
        host = host[4:]
    if "/" in host:
        host = host.split("/")[0]
    return host


def parse_company_input(company: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Return (domain, company_name) for Hunter Domain Search.
    """
    token = company.strip()
    if not token:
        return None, None

    # If it contains dots, treat it as a URL/domain.
    if "." in token or "://" in token:
        domain = normalize_domain(token)
        return (domain or None), None

    # Otherwise send as company name.
    return None, token


def domain_search(company: str, limit: int = 5) -> Dict[str, Any]:
    """
    Query Hunter Domain Search by domain or company name.
    """
    if not HUNTER_API_KEY:
        return {
            "success": False,
            "error": "HUNTER_API_KEY not configured. Set it in your .env file.",
            "data": None,
        }

    domain, company_name = parse_company_input(company)
    if not domain and not company_name:
        return {
            "success": False,
            "error": "Company input is empty or invalid.",
            "data": None,
        }

    params: Dict[str, Any] = {
        "api_key": HUNTER_API_KEY,
        "limit": max(1, min(limit, 10)),
        "required_field": "position",
    }
    if domain:
        params["domain"] = domain
    else:
        params["company"] = company_name

    url = f"{HUNTER_BASE_URL}/domain-search"

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data", {})

        return {
            "success": True,
            "data": data,
            "meta": payload.get("meta", {}),
            "request": {"domain": domain, "company": company_name},
        }
    except requests.exceptions.RequestException as exc:
        return {
            "success": False,
            "error": str(exc),
            "data": None,
        }


def company_enrichment(domain: str) -> Dict[str, Any]:
    """
    Fetch company-level data for a domain (description, size, location, etc.).
    """
    if not HUNTER_API_KEY:
        return {
            "success": False,
            "error": "HUNTER_API_KEY not configured. Set it in your .env file.",
            "data": None,
        }

    normalized = normalize_domain(domain)
    if not normalized:
        return {
            "success": False,
            "error": "Domain is empty or invalid for company enrichment.",
            "data": None,
        }

    url = f"{HUNTER_BASE_URL}/companies/find"
    params = {
        "api_key": HUNTER_API_KEY,
        "domain": normalized,
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()
        return {
            "success": True,
            "data": payload.get("data", {}),
            "meta": payload.get("meta", {}),
        }
    except requests.exceptions.RequestException as exc:
        return {
            "success": False,
            "error": str(exc),
            "data": None,
        }
