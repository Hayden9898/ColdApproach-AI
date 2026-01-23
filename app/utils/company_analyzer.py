"""
Company size analysis using Apollo employee count data.
Categorizes companies and provides prioritized role arrays.
"""
from typing import List, Dict, Any, Optional


def categorize_company_size(employee_count: Optional[int]) -> str:
    """
    Categorize company size based on employee count from Apollo.
    
    Categories:
    - small: 1-30 employees
    - medium: 30-100 employees  
    - large: 100+ employees
    
    Args:
        employee_count: Number of employees (from Apollo)
    
    Returns:
        "small", "medium", "large", or "unknown"
    """
    if employee_count is None:
        return "unknown"
    
    if employee_count <= 30:
        return "small"
    elif employee_count <= 100:
        return "medium"
    else:
        return "large"


def get_prioritized_roles_by_size(employee_count: Optional[int]) -> List[str]:
    """
    Get prioritized array of job titles based on company size.
    
    Roles are ordered by importance/priority for outreach.
    
    Strategy:
    - Small (1-30): Decision makers first (CTO, Founders, CEO)
    - Medium (30-100): Hiring managers (Lead Engineers, Engineering Managers)
    - Large (100+): Recruiters and talent acquisition
    
    Args:
        employee_count: Number of employees from Apollo
    
    Returns:
        Prioritized list of job titles (most important first)
    """
    size = categorize_company_size(employee_count)
    
    # Prioritized role arrays - ordered by importance
    role_priorities = {
        "small": [
            # 1-30 employees: Direct Decision Makers
            "Founder",
            "CTO",
            "CEO",
            "Co-Founder",
            "Co-founder",
            "Chief Technology Officer",
            "Chief Executive Officer",
            "Technical Co-Founder",
        ],
        "medium": [
            # 31-100 employees: Hiring Managers & Directors
            "VP Engineering",
            "Head of Talent",
            "Director",
            "Director of Engineering",
            "Head of Engineering",
            "VP of Engineering",
            "Engineering Director",
            "Talent Director",
            "Director of Talent",
        ],
        "large": [
            # 100+ employees: Individual Contributors (Recruiters)
            "Recruiter",
            "Talent Acquisition",
            "Technical Recruiter",
            "Senior Recruiter",
            "Talent Acquisition Specialist",
            "Recruiting Coordinator",
            "Talent Sourcer",
            "Technical Talent Acquisition",
        ],
        "unknown": [
            # Fallback - try decision makers first
            "Founder",
            "CTO",
            "CEO",
            "VP Engineering",
            "Head of Talent",
            "Director",
        ]
    }
    
    return role_priorities.get(size, role_priorities["unknown"])


def analyze_company_from_apollo(company_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze company using Apollo data and return prioritized roles.
    
    Args:
        company_data: Company data from Apollo search_company_by_domain()
    
    Returns:
        Analysis with size, employee count, and prioritized roles
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
            "small": "Target decision makers (CTO, Founders) - they make hiring decisions directly",
            "medium": "Target hiring managers (Lead/Senior Engineers) - they evaluate candidates",
            "large": "Target recruiters (Talent Acquisition) - they source and screen candidates",
            "unknown": "Target decision makers (fallback strategy)"
        }.get(size, "Target decision makers")
    }
