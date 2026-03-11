"""
Company size analysis and role ranking for outreach targeting.
"""
from typing import Any, Dict, List, Optional


ROLE_PRIORITIES_BY_SIZE = {
    # Small startups: CEO/Founder is the decision-maker.
    "small_1_10": [
        "CEO",
        "President",
        "Co-Founder",
        "Cofounder",
        "Founder",
        "Technical Co-Founder",
        "CTO",
        "COO",
        "CPO",
        "Chief of Staff",
        "Founding Engineer",
        "Head of Engineering",
        "Head of Product",
        "Head of People",
        "Head of Talent",
        "Head of Growth",
        "Head of Operations",
        "VP Engineering",
        "VP Talent",
        "VP Product",
        "VP Technology",
        "Director of Engineering",
        "Engineering Director",
        "Director of Product",
        "Engineering Manager",
        "Tech Lead",
        "Lead Engineer",
        "Project Lead",
        "Hiring Manager",
        "Technical Recruiter",
        "Talent Acquisition",
        "Recruiting Manager",
        "Talent Partner",
        "Senior Recruiter",
        "Recruiter",
        "People Operations",
        "Member of Technical Staff",
    ],
    # Mid-size: CTO/senior technical first, CEO for forward-to-eng effect.
    "mid_11_50": [
        "CTO",
        "VP Engineering",
        "VP Technology",
        "Head of Engineering",
        "CEO",
        "President",
        "Co-Founder",
        "Cofounder",
        "Founder",
        "Technical Co-Founder",
        "COO",
        "CPO",
        "Chief of Staff",
        "CRO",
        "CMO",
        "Head of Product",
        "Head of People",
        "Head of Talent",
        "Head of Growth",
        "Head of Operations",
        "VP Product",
        "VP Operations",
        "VP People",
        "VP Talent",
        "Engineering Director",
        "Director of Engineering",
        "Director of Product",
        "Director of Talent",
        "Director of People",
        "Director of Operations",
        "Engineering Manager",
        "Tech Lead",
        "Lead Engineer",
        "Project Lead",
        "Hiring Manager",
        "Technical Recruiter",
        "Talent Acquisition",
        "Recruiting Manager",
        "Talent Partner",
        "Senior Recruiter",
        "Recruiter",
        "People Operations",
        "Founding Engineer",
        "Member of Technical Staff",
    ],
    # Large orgs: recruiter/talent first
    "large_50_plus": [
        "Technical Recruiter",
        "Talent Acquisition",
        "Recruiting Manager",
        "Talent Partner",
        "Senior Recruiter",
        "Recruiter",
        "Sourcer",
        "University Recruiter",
        "Hiring Manager",
        "People Operations",
        "Engineering Manager",
        "Director of Engineering",
        "Engineering Director",
        "Director of Product",
        "Director of Talent",
        "Director of People",
        "Director of Operations",
        "VP Engineering",
        "VP Technology",
        "VP Product",
        "VP Operations",
        "VP People",
        "VP Talent",
        "Head of Engineering",
        "Head of Product",
        "Head of People",
        "Head of Talent",
        "Head of Growth",
        "Head of Operations",
        "CTO",
        "CEO",
        "COO",
        "CPO",
        "Chief of Staff",
        "Managing Director",
        "General Manager",
        "President",
        "CRO",
        "CMO",
        "CIO",
        "CDO",
        "Co-Founder",
        "Cofounder",
        "Founder",
        "Technical Co-Founder",
        "Tech Lead",
        "Lead Engineer",
        "Project Lead",
        "Member of Technical Staff",
    ],
    # Unknown size: comprehensive catch-all, CEO/Founder first.
    "unknown": [
        "CEO",
        "President",
        "Co-Founder",
        "Cofounder",
        "Founder",
        "Technical Co-Founder",
        "CTO",
        "COO",
        "CPO",
        "Chief of Staff",
        "Founding Engineer",
        "CRO",
        "CMO",
        "Head of Engineering",
        "Head of Product",
        "Head of People",
        "Head of Talent",
        "Head of Growth",
        "Head of Operations",
        "VP Engineering",
        "VP Product",
        "VP Technology",
        "VP Operations",
        "VP People",
        "VP Talent",
        "Director of Engineering",
        "Engineering Director",
        "Director of Product",
        "Director of Talent",
        "Director of People",
        "Director of Operations",
        "Engineering Manager",
        "Tech Lead",
        "Lead Engineer",
        "Project Lead",
        "Hiring Manager",
        "Technical Recruiter",
        "Talent Acquisition",
        "Recruiting Manager",
        "Talent Partner",
        "Senior Recruiter",
        "Recruiter",
        "People Operations",
        "Member of Technical Staff",
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
            "small_1_10": "Prefer CEO/founders — they are the decision-makers.",
            "mid_11_50": "Prefer CTO/senior technical leaders, CEO for forward-to-engineering effect.",
            "large_50_plus": "Prefer recruiters and hiring managers — CEO is unreachable at this size.",
            "unknown": "Comprehensive targeting — CEO/founders first, then technical leaders and recruiters.",
        }.get(size, "Comprehensive targeting — CEO/founders first, then technical leaders and recruiters."),
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
