import io
import re
from typing import Dict, Optional, List

import pdfplumber


def extract_resume_text(file_bytes: bytes) -> Dict[str, str]:
    """
    Extract raw text from a PDF resume.

    Raises:
        RuntimeError: If the PDF cannot be read or contains no text.
    """
    if not file_bytes:
        raise RuntimeError("Uploaded PDF is empty.")

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text_parts = []
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(page_text.strip())

        extracted_text = "\n\n".join(text_parts).strip()
    except Exception as exc:  # pragma: no cover - library-specific failures
        raise RuntimeError("Unable to read PDF. Please upload a valid document.") from exc

    if not extracted_text:
        raise RuntimeError("No readable text found in the PDF.")

    return {"text": extracted_text}


def is_resume(resume_text: str) -> bool:
    """
    Validate if the extracted text appears to be a resume.
    
    Checks for common resume indicators:
    - Resume sections (Education, Experience, Skills, etc.)
    - Common resume keywords
    - Reasonable structure
    
    Args:
        resume_text: Raw text extracted from PDF
    
    Returns:
        True if text appears to be a resume, False otherwise
    """
    if not resume_text or len(resume_text.strip()) < 50:
        return False
    
    text_lower = resume_text.lower()
    
    # Check for common resume sections
    resume_sections = [
        'education', 'experience', 'work experience', 'employment',
        'skills', 'technical skills', 'qualifications',
        'summary', 'objective', 'about', 'profile'
    ]
    
    section_count = sum(1 for section in resume_sections if section in text_lower)
    
    # Check for common resume keywords
    resume_keywords = [
        'university', 'college', 'degree', 'bachelor', 'master',
        'intern', 'engineer', 'developer', 'software', 'programming',
        'gpa', 'graduated', 'certification', 'project'
    ]
    
    keyword_count = sum(1 for keyword in resume_keywords if keyword in text_lower)
    
    # Must have at least 2 resume sections OR 3+ keywords to be considered a resume
    # This helps filter out random PDFs, invoices, documents, etc.
    return section_count >= 2 or keyword_count >= 3


def format_resume(resume_text: str) -> Dict[str, any]:
    """
    Format raw resume text into a structured object.
    Works with general resume formats.
    
    Args:
        resume_text: Raw text extracted from PDF resume
    
    Returns:
        Dictionary with structured resume data:
        - name: Full name
        - email: Email address
        - phone: Phone number (optional)
        - skills: List of technical skills
        - experience: List of work experience entries
        - education: List of education entries
        - summary: Professional summary/about section (optional)
    """
    lines = resume_text.split('\n')
    formatted = {
        "name": None,
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
        "skills": [],
        "experience": [],
        "education": [],
        "summary": None
    }
    
    # Extract name (usually first non-empty line)
    for line in lines[:5]:  # Check first 5 lines
        line = line.strip()
        if line and not _is_email(line) and not _is_url(line) and not _is_date_range(line):
            # Simple heuristic: name is usually 2-4 words, capitalized
            words = line.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() if w else False for w in words):
                formatted["name"] = line
                break
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, resume_text)
    if email_match:
        formatted["email"] = email_match.group()
    

    # Extract linkedin
    linkedin_pattern = r'linkedin\.com/in/[a-zA-Z0-9-]+'
    linkedin_match = re.search(linkedin_pattern, resume_text)
    if linkedin_match:
        formatted["linkedin"] = linkedin_match.group()
    
    # Extract github
    github_pattern = r'github\.com/[a-zA-Z0-9-]+'
    github_match = re.search(github_pattern, resume_text)
    if github_match:
        formatted["github"] = github_match.group()
    
    # Extract phone (optional)
    phone_patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890 or 123-456-7890
        r'\+\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1 (123) 456-7890
    ]
    for pattern in phone_patterns:
        phone_match = re.search(pattern, resume_text)
        if phone_match:
            formatted["phone"] = phone_match.group().strip()
            break
    
    # Extract sections
    sections = _parse_sections(resume_text)
    
    # Extract skills
    skills_section = _find_section(sections, ['skills', 'technical skills', 'technical', 'technologies'])
    if skills_section:
        formatted["skills"] = _extract_skills(skills_section)
    
    # Extract experience
    exp_section = _find_section(sections, ['experience', 'work experience', 'employment', 'work history'])
    if exp_section:
        formatted["experience"] = _extract_experience(exp_section)
    
    # Extract education
    edu_section = _find_section(sections, ['education', 'academic', 'qualifications'])
    if edu_section:
        formatted["education"] = _extract_education(edu_section)
    
    # Extract summary (optional)
    summary_section = _find_section(sections, ['summary', 'about', 'profile', 'objective'])
    if summary_section:
        formatted["summary"] = _extract_summary(summary_section)
    
    return formatted


def _is_email(text: str) -> bool:
    """Check if text is an email address."""
    return '@' in text and '.' in text.split('@')[1] if '@' in text else False


def _is_url(text: str) -> bool:
    """Check if text is a URL."""
    return text.startswith(('http://', 'https://', 'www.', 'linkedin.com', 'github.com'))


def _is_date_range(text: str) -> bool:
    """Check if text looks like a date range."""
    date_patterns = [
        r'\d{4}\s*[-–—]\s*(Present|Current|\d{4})',
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*[-–—]\s*(Present|Current|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in date_patterns)


def _parse_sections(resume_text: str) -> Dict[str, str]:
    """Parse resume into sections based on common headers."""
    sections = {}
    lines = resume_text.split('\n')
    
    current_section = None
    current_content = []
    
    # Common section headers (ordered by specificity - longer/more specific first)
    # Note: "languages" is NOT here because it's a category within skills, not a section header
    section_keywords = [
        'work experience', 'technical skills', 'work history',
        'education', 'experience', 'employment',
        'skills', 'technical', 'technologies', 'competencies',
        'summary', 'about', 'profile', 'objective', 'projects', 'achievements',
        'certifications', 'publications', 'awards'
    ]
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Check if this line is a section header
        is_header = False
        line_lower = line_stripped.lower()
        for keyword in section_keywords:
            # Match exact, starts with keyword, or keyword is contained (handles "Technical Skills" matching "technical skills")
            # Check exact match first, then prefix match, then contains
            if (line_lower == keyword or 
                line_lower.startswith(keyword + ' ') or 
                line_lower.startswith(keyword + ':') or
                (len(keyword) > 5 and keyword in line_lower)):  # Only use contains for longer keywords to avoid false matches
                is_header = True
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                # Start new section - use the matched keyword for consistency
                current_section = keyword.lower()
                current_content = []
                break
        
        if not is_header and current_section:
            current_content.append(line_stripped)
        elif not is_header and not current_section:
            # Content before first section (header/contact info)
            if 'header' not in sections:
                sections['header'] = []
            if isinstance(sections.get('header'), list):
                sections['header'].append(line_stripped)
    
    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_content)
    
    return sections


def _find_section(sections: Dict[str, str], keywords: List[str]) -> Optional[str]:
    """Find a section by keywords."""
    for keyword in keywords:
        for section_name, content in sections.items():
            if keyword.lower() in section_name.lower():
                return content
    return None


def _extract_skills(skills_text: str) -> List[str]:
    """Extract skills from skills section.
    
    Handles dynamic category headers like:
    - Languages: Python, JavaScript, C++
    - Libraries/Frameworks: Django, React, Node.js
    - Backend: Node.js, Express
    - Frontend: React, Vue
    - Tools: Git, Docker
    
    Extracts all skills from all categories and combines into one array.
    """
    skills = []
    lines = skills_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('•') or line.startswith('-'):
            continue
        
        # Handle format like "Category: item1, item2, item3" or "Category/Subcategory: items"
        if ':' in line:
            # Split on colon, take everything after it (the actual skills)
            parts = line.split(':', 1)
            if len(parts) == 2:
                skills_part = parts[1].strip()
                
                # Split by common delimiters
                if ',' in skills_part:
                    items = [item.strip() for item in skills_part.split(',')]
                    skills.extend(items)
                elif '|' in skills_part:
                    items = [item.strip() for item in skills_part.split('|')]
                    skills.extend(items)
                else:
                    # Single skill after colon
                    if skills_part and len(skills_part) < 50:
                        skills.append(skills_part)
        # Handle format without category header (just comma-separated list)
        elif ',' in line:
            items = [item.strip() for item in line.split(',')]
            skills.extend(items)
        elif '|' in line:
            items = [item.strip() for item in line.split('|')]
            skills.extend(items)
        elif '•' in line or '-' in line:
            # Bullet point format
            items = re.split(r'[•\-]\s*', line)
            skills.extend([item.strip() for item in items if item.strip()])
        else:
            # Single skill per line (if reasonable length)
            if line and len(line) < 50:
                skills.append(line)
    
    # Clean and deduplicate
    cleaned_skills = []
    seen = set()
    for skill in skills:
        skill_clean = skill.strip().strip('•').strip('-').strip()
        # Filter out empty strings and very short items
        if skill_clean and len(skill_clean) > 1 and skill_clean.lower() not in seen:
            # Filter out common non-skill words that might slip through
            if skill_clean.lower() not in ['and', 'or', 'the', 'a', 'an']:
                cleaned_skills.append(skill_clean)
                seen.add(skill_clean.lower())
    
    return cleaned_skills[:50]  # Increased limit to 50 skills


def _extract_experience(exp_text: str) -> List[Dict[str, str]]:
    """Extract work experience entries.
    
    Expected format:
    Job Title Date Range
    Company Location
    • Bullet points
    """
    experiences = []
    lines = exp_text.split('\n')
    
    current_exp = {}
    current_exp['description'] = []
    current_bullets = []
    expecting_company = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # Check if line starts with bullet point
        if line.startswith('•') or line.startswith('-'):
            bullet = line.lstrip('•').lstrip('-').strip()
            if bullet:
                current_bullets.append(bullet)
            continue
        
        # Check if line is a date range (contains month names or "Present")
        if _is_date_range(line):
            # This is likely the title + date line
            # Pattern: "Software Engineer Intern Dec 2025 – Present"
            # Extract title (everything before the date)
            date_match = re.search(r'((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|\d{4}\s*[-–—])', line, re.IGNORECASE)
            if date_match:
                date_start = date_match.start()
                title = line[:date_start].strip()
                duration = line[date_start:].strip()
                
                # Save previous experience if exists
                if current_exp and (current_exp.get('title') or current_exp.get('company')):
                    if current_bullets:
                        current_exp['description'].extend(current_bullets)
                    experiences.append(current_exp)
                
                # Start new experience
                current_exp = {'title': title, 'duration': duration, 'description': []}
                current_bullets = []
                expecting_company = True
            continue
        
        # If we're expecting company name (line after title+date)
        if expecting_company:
            # This should be "Company Location" or just "Company"
            # Try to split on common patterns
            parts = re.split(r'\s+([A-Z][a-z]+,\s*[A-Z]{2})$', line)  # Match "City, ST" at end
            if len(parts) >= 2:
                current_exp['company'] = parts[0].strip()
                current_exp['location'] = parts[1].strip()
            else:
                current_exp['company'] = line
            expecting_company = False
            continue
    
    # Save last experience
    if current_exp and (current_exp.get('title') or current_exp.get('company')):
        if current_bullets:
            current_exp['description'].extend(current_bullets)
        experiences.append(current_exp)
    
    return experiences[:10]  # Limit to top 10 experiences


def _extract_education(edu_text: str) -> List[Dict[str, str]]:
    """Extract education entries.
    
    Expected format:
    School Name Date Range
    Degree Info (GPA: X.X/X.X) Location
    """
    education = []
    lines = edu_text.split('\n')
    
    current_edu = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('•') or line.startswith('-'):
            continue
        
        # Check if line has a school name (usually contains "University", "College", "School")
        # And might have date range: "McMaster University Sep 2024 - May 2027"
        if any(word in line.lower() for word in ['university', 'college', 'school', 'institute']):
            if current_edu and current_edu.get('school'):
                # Save previous education
                education.append(current_edu)
                current_edu = {}
            
            # Extract school name and date range
            date_match = re.search(r'((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*[-–—]\s*(May|Present|Current|\d{4}))', line, re.IGNORECASE)
            if date_match:
                date_start = date_match.start()
                current_edu['school'] = line[:date_start].strip()
                current_edu['duration'] = line[date_start:].strip()
            else:
                current_edu['school'] = line
        elif 'gpa' in line.lower():
            # Extract GPA: "Honours Computer Science Co-op, Bachelor of Applied Science (GPA: 3.9/4.0) Hamilton, ON"
            gpa_match = re.search(r'\(GPA:\s*([\d.]+/[\d.]+)\)', line, re.IGNORECASE)
            if gpa_match:
                current_edu['gpa'] = gpa_match.group(1)
            
            # Extract degree (everything before GPA)
            if gpa_match:
                degree_part = line[:gpa_match.start()].strip()
                # Remove trailing comma if present
                degree_part = degree_part.rstrip(',').strip()
                current_edu['degree'] = degree_part
            
            # Extract location (after GPA)
            if gpa_match:
                location_part = line[gpa_match.end():].strip()
                # Remove parentheses and clean
                location_part = re.sub(r'^[()\s]+', '', location_part).strip()
                if location_part:
                    current_edu['location'] = location_part
        elif not current_edu.get('degree') and len(line) > 10:
            # Might be degree info (if no GPA in line)
            current_edu['degree'] = line
    
    # Save last education
    if current_edu and current_edu.get('school'):
        education.append(current_edu)
    
    return education[:5]  # Limit to top 5 education entries


def _extract_summary(summary_text: str) -> str:
    """Extract summary/about section."""
    # Clean up the summary text
    lines = summary_text.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('•')]
    summary = ' '.join(cleaned_lines)
    
    # Limit length
    if len(summary) > 500:
        summary = summary[:500] + "..."
    
    return summary


def extract_structured_data(resume_text: str) -> Dict[str, any]:
    """
    Alias for format_resume for backward compatibility.
    """
    return format_resume(resume_text)