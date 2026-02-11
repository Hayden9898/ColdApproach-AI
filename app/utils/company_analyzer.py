"""
Company size analysis and role ranking for outreach targeting.
"""
from typing import Any, Dict, List, Optional


ROLE_PRIORITIES_BY_SIZE = {
    # Smaller startups: decision makers can hire directly.
    "small_1_10": [
        "Co-Founder",
        "Cofounder",
        "Founder",
        "CTO",
        "CEO",
        "Technical Co-Founder",
        "Founding Engineer",
        "Head of Engineering",
    ],
    # Growth startups: still technical leaders, plus hiring owners.
    "mid_11_50": [
        "CTO",
        "VP Engineering",
        "Head of Engineering",
        "Engineering Director",
        "Director of Engineering",
        "Engineering Manager",
        "Tech Lead",
        "Lead Engineer",
        "Project Lead",
        "Founder",
    ],
    # Larger orgs: recruiting and org managers become better entry points.
    "large_50_plus": [
        "Technical Recruiter",
        "Talent Acquisition",
        "Senior Recruiter",
        "Recruiter",
        "Hiring Manager",
        "Engineering Manager",
        "Director of Engineering",
        "VP Engineering",
        "Head of Engineering",
    ],
    "unknown": [
        "CTO",
        "Founder",
        "Head of Engineering",
        "Engineering Manager",
        "Technical Recruiter",
    ],
}


def _normalize_headcount(employee_count: Any) -> Optional[int]:
    """
    Convert Hunter headcount values to a representative integer when possible.

    Examples:
    - 12 -> 12
    - "11-50" -> 50
    - "50+" -> 50
    """
    if employee_count is None:
        return None

    if isinstance(employee_count, int):
        return employee_count

    if isinstance(employee_count, str):
        value = employee_count.strip()
        if not value:
            return None
        if "-" in value:
            end = value.split("-")[-1]
            try:
                return int(end)
            except ValueError:
                return None
        if value.endswith("+"):
            try:
                return int(value[:-1])
            except ValueError:
                return None
        try:
            return int(value)
        except ValueError:
            return None

    return None


def categorize_company_size(employee_count: Any) -> str:
    """
    Categorize company size based on employee count.

    Categories:
    - small_1_10: 1-10 employees
    - mid_11_50: 11-50 employees
    - large_50_plus: 50+ employees
    """
    normalized = _normalize_headcount(employee_count)
    if normalized is None:
        return "unknown"

    if normalized <= 10:
        return "small_1_10"
    if normalized <= 50:
        return "mid_11_50"
    if normalized > 50:
        return "large_50_plus"
    return "unknown"


def get_prioritized_roles_by_size(employee_count: Any) -> List[str]:
    """
    Get prioritized outreach roles for configured company size ranges.
    """
    size = categorize_company_size(employee_count)
    return ROLE_PRIORITIES_BY_SIZE.get(size, ROLE_PRIORITIES_BY_SIZE["unknown"])


def analyze_company(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze company data and return outreach role strategy.
    """
    employee_count = company_data.get("employee_count")
    size = categorize_company_size(employee_count)
    prioritized_roles = get_prioritized_roles_by_size(employee_count)

    return {
        "company_name": company_data.get("name"),
        "employee_count": employee_count,
        "size_category": size,
        "prioritized_roles": prioritized_roles,
        "strategy": {
            "small_1_10": "Prefer founders/CTO for direct startup decision-makers.",
            "mid_11_50": "Prefer CTO/VP/engineering leaders and project leads.",
            "large_50_plus": "Prefer technical recruiters and hiring managers first.",
            "unknown": "Prefer technical decision-makers, then engineering managers.",
        }.get(size, "Prefer technical decision-makers."),
    }


def score_contact(title: Optional[str], prioritized_roles: List[str]) -> int:
    """
    Score a contact title against prioritized role targets.
    Higher score means better fit.
    """
    if not title:
        return 0

    normalized_title = title.lower()
    score = 0

    for idx, role in enumerate(prioritized_roles):
        role_lower = role.lower()
        if role_lower in normalized_title:
            # Earlier role in priority list receives higher weight.
            score = max(score, len(prioritized_roles) - idx)

    return score


def role_priority_config() -> Dict[str, List[str]]:
    """
    Expose role-priority config so callers can adjust behavior easily.
    """
    return ROLE_PRIORITIES_BY_SIZE
