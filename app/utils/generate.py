from typing import Any, Dict, List, Optional


def get_client():
    """
    Lazy-load OpenAI client to avoid crashing app on import when key is missing.
    """
    from openai import OpenAI

    return OpenAI()


# ---------------------------------------------------------------------------
# Context builder (shared by all generation modes)
# ---------------------------------------------------------------------------

def _build_context_sections(
    scraped_data: Dict[str, Any],
    company_data: Optional[Dict[str, Any]] = None,
    resume_data: Optional[Dict[str, Any]] = None,
    contact_data: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    Build context sections from all data sources.
    Returns a list of section strings (joined later by each prompt builder).
    """
    url = scraped_data.get("url", "Unknown URL")
    blocked = scraped_data.get("blocked")
    title = scraped_data.get("title")
    description = scraped_data.get("description")
    og_description = scraped_data.get("og_description")
    h1_list = scraped_data.get("h1") or []
    summary_keywords = scraped_data.get("summary_keywords") or []
    error = scraped_data.get("error")

    sections: List[str] = [f"Company URL: {url}"]

    if blocked is True:
        sections.append(
            "The website returned a blocking or anti-bot page. Infer the company's focus using the metadata below."
        )
    elif blocked is False:
        sections.append("The website loaded successfully; use the extracted content below.")

    if error:
        sections.append(f"Scraping Error: {error}")

    if title:
        sections.append(f"Page Title: {title}")

    if description:
        sections.append(f"Meta Description: {description}")

    if og_description:
        sections.append(f"OpenGraph Description: {og_description}")

    if h1_list:
        formatted_h1 = "\n".join(f"- {h}" for h in h1_list)
        sections.append(f"H1 Headlines:\n{formatted_h1}")

    if summary_keywords:
        keywords = ", ".join(summary_keywords[:20])
        sections.append(f"High-value Keywords: {keywords}")

    # --- Hunter company data ---
    if company_data:
        company_parts = []
        if company_data.get("name"):
            company_parts.append(f"Company Name: {company_data['name']}")
        if company_data.get("industry"):
            company_parts.append(f"Industry: {company_data['industry']}")
        if company_data.get("description"):
            company_parts.append(f"Company Description: {company_data['description']}")
        if company_data.get("employee_count"):
            company_parts.append(f"Company Size: {company_data['employee_count']} employees")
        if company_parts:
            sections.append("--- Company Info (from database) ---\n" + "\n".join(company_parts))

    # --- Contact data ---
    if contact_data:
        contact_parts = []
        if contact_data.get("name"):
            contact_parts.append(f"Recipient Name: {contact_data['name']}")
        if contact_data.get("title"):
            contact_parts.append(f"Recipient Role: {contact_data['title']}")
        if contact_data.get("seniority"):
            contact_parts.append(f"Seniority Level: {contact_data['seniority']}")
        if contact_parts:
            sections.append("--- Recipient ---\n" + "\n".join(contact_parts))

    # --- Resume / sender profile ---
    if resume_data:
        resume_parts = []
        if resume_data.get("name"):
            resume_parts.append(f"Sender Name: {resume_data['name']}")
        if resume_data.get("summary"):
            resume_parts.append(f"Professional Summary: {resume_data['summary']}")

        skills = resume_data.get("skills") or []
        if skills:
            company_kw_lower = {kw.lower() for kw in summary_keywords}
            matching = [s for s in skills if s.lower() in company_kw_lower]
            other = [s for s in skills if s.lower() not in company_kw_lower]
            if matching:
                resume_parts.append(f"Relevant Skills (match company): {', '.join(matching[:10])}")
            if other:
                resume_parts.append(f"Other Skills: {', '.join(other[:10])}")

        experience = resume_data.get("experience") or []
        for i, exp in enumerate(experience[:4]):
            exp_title = exp.get("title", "")
            exp_company = exp.get("company", "")
            exp_duration = exp.get("duration", "")
            bullets = exp.get("description") or []
            exp_str = f"Experience {i+1}: {exp_title} at {exp_company} ({exp_duration})"
            if bullets:
                exp_str += "\n  " + "\n  ".join(bullets[:3])
            resume_parts.append(exp_str)

        projects = resume_data.get("projects") or []
        for i, proj in enumerate(projects[:5]):
            proj_str = f"Project {i+1}: {proj.get('name', '')}"
            if proj.get("technologies"):
                proj_str += f" ({proj['technologies']})"
            if proj.get("duration"):
                proj_str += f" — {proj['duration']}"
            bullets = proj.get("description") or []
            if bullets:
                proj_str += "\n  " + "\n  ".join(bullets[:3])
            resume_parts.append(proj_str)

        education = resume_data.get("education") or []
        for edu in education[:1]:
            edu_str = f"Education: {edu.get('degree', '')} — {edu.get('school', '')}"
            if edu.get("gpa"):
                edu_str += f" (GPA: {edu['gpa']})"
            resume_parts.append(edu_str)

        if resume_parts:
            sections.append("--- Sender Profile (your resume) ---\n" + "\n".join(resume_parts))

    return sections


# ---------------------------------------------------------------------------
# From-scratch prompt (existing behaviour, future ML mode foundation)
# ---------------------------------------------------------------------------

def generate_prompt(
    scraped_data: Dict[str, Any],
    company_data: Optional[Dict[str, Any]] = None,
    resume_data: Optional[Dict[str, Any]] = None,
    contact_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build a structured prompt from scraped website data, Hunter company data,
    the user's resume profile, and the target contact.
    """
    sections = _build_context_sections(scraped_data, company_data, resume_data, contact_data)

    # --- Final instructions ---
    tone_note = ""
    if contact_data and contact_data.get("seniority"):
        seniority = contact_data["seniority"].lower()
        if seniority in ("executive", "senior"):
            tone_note = "- Tone: direct and respectful — they're busy decision-makers\n"
        elif seniority in ("junior", "entry"):
            tone_note = "- Tone: friendly and peer-level\n"
        else:
            tone_note = "- Tone: professional but approachable\n"

    sections.append(
        "Write a personalized cold outreach email for a software engineering opportunity.\n"
        "Return your response in EXACTLY this format:\n"
        "SUBJECT: <subject line here>\n"
        "BODY:\n"
        "<email body here>\n\n"
        "Requirements:\n"
        "- Subject line: short, specific to the company, no clickbait\n"
        "- Body: 4–6 sentences (under 120 words)\n"
        "- Start with a specific insight about the company's product, tech, or mission — not a generic compliment\n"
        + (
            "- Connect the sender's most relevant skills or experiences to the company's work. "
            "Prioritize more recent internships and work experience. "
            "However, if a personal/academic project is exceptionally strong or directly relevant "
            "to what this company builds, include it alongside the experience.\n"
            if resume_data
            else ""
        )
        + tone_note
        + "- Sound human and natural, not templated\n"
        "- Avoid buzzwords (synergy, leverage, exciting opportunity, passionate)\n"
        "- End with a soft CTA asking for a quick chat\n"
        "- No greeting line (no 'Hi X,' or 'Dear X,') — just the body\n"
        "- No signature or sign-off"
    )

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------

def _resolve_link_urls(
    resume_data: Optional[Dict[str, Any]] = None,
    linkedin_url: Optional[str] = None,
    github_url: Optional[str] = None,
) -> Dict[str, str]:
    """Resolve final LinkedIn and GitHub URLs from explicit args or resume data."""
    linkedin = linkedin_url or ""
    if not linkedin and resume_data and resume_data.get("linkedin"):
        linkedin = resume_data["linkedin"]
        if not linkedin.startswith("http"):
            linkedin = f"https://{linkedin}"

    github = github_url or ""
    if not github and resume_data and resume_data.get("github"):
        github = resume_data["github"]
        if not github.startswith("http"):
            github = f"https://{github}"

    return {"linkedin_url": linkedin, "github_url": github}


def _fill_deterministic_placeholders(
    template: str,
    company_data: Optional[Dict[str, Any]] = None,
    contact_data: Optional[Dict[str, Any]] = None,
    resume_data: Optional[Dict[str, Any]] = None,
    linkedin_url: Optional[str] = None,
    github_url: Optional[str] = None,
    strip_link_placeholders: bool = False,
) -> str:
    """
    First pass: replace placeholders that have exact known values.
    Leaves contextual placeholders (e.g. [specific company detail]) for GPT.

    When strip_link_placeholders=True, removes [LinkedIn] and [GitHub]
    placeholders from the body entirely (links go in the HTML footer instead).
    """
    filled = template

    # Company Name
    company_name = ""
    if company_data and company_data.get("name"):
        company_name = company_data["name"]
    filled = filled.replace("[Company Name]", company_name)

    # Contact First Name
    first_name = ""
    if contact_data and contact_data.get("name"):
        first_name = contact_data["name"].split()[0]
    filled = filled.replace("[First Name]", first_name)

    # Sender Name
    sender_name = ""
    if resume_data and resume_data.get("name"):
        sender_name = resume_data["name"]
    filled = filled.replace("[Sender Name]", sender_name)

    # LinkedIn / GitHub
    urls = _resolve_link_urls(resume_data, linkedin_url, github_url)

    if strip_link_placeholders:
        # Remove placeholders and surrounding link-intro text
        import re
        filled = filled.replace("[LinkedIn]", "")
        filled = filled.replace("[GitHub]", "")
        # Clean up lines like "Here are my links:" or "Links:" left empty
        filled = re.sub(r"(?m)^.*(?:links?|profiles?)\s*:?\s*\|\s*$", "", filled, flags=re.IGNORECASE)
        filled = re.sub(r"(?m)^.*(?:links?|profiles?)\s*:?\s*$", "", filled, flags=re.IGNORECASE)
        # Collapse excessive blank lines left behind
        filled = re.sub(r"\n{3,}", "\n\n", filled)
    else:
        filled = filled.replace("[LinkedIn]", urls["linkedin_url"])
        filled = filled.replace("[GitHub]", urls["github_url"])

    return filled


def generate_template_prompt(
    pre_filled_template: str,
    scraped_data: Dict[str, Any],
    company_data: Optional[Dict[str, Any]] = None,
    resume_data: Optional[Dict[str, Any]] = None,
    contact_data: Optional[Dict[str, Any]] = None,
    smooth_grammar: bool = True,
) -> str:
    """
    Build a prompt that instructs GPT to fill contextual placeholders
    in a pre-filled template using the scraped/company/resume context.

    When smooth_grammar is True, GPT may make minor grammar adjustments
    around placeholders for natural flow. When False, GPT must not
    modify any text outside the brackets.
    """
    sections = _build_context_sections(scraped_data, company_data, resume_data, contact_data)

    if smooth_grammar:
        structure_rules = (
            "- You may make minor grammar adjustments to words immediately surrounding a placeholder "
            "so the sentence reads naturally (e.g. fix article agreement, verb tense, possessives)\n"
            "- Do NOT change the overall structure, tone, or meaning of any sentence\n"
            "- Do NOT add new sentences, remove sentences, or rearrange paragraphs\n"
        )
    else:
        structure_rules = (
            "- Do NOT modify any text outside the brackets — keep every word exactly as written\n"
            "- Keep the template's tone and structure exactly as written\n"
        )

    sections.append(
        "You have been given a partially filled email template below. "
        "Your job is to fill in the remaining bracketed placeholders "
        "(like [specific company detail], [company focus area], [resume highlights - bullet points]) "
        "using the context data provided above.\n\n"
        "Rules:\n"
        "- Replace each bracketed placeholder with specific, relevant content from the context\n"
        "- For [resume highlights - bullet points], prioritize more recent internships and work experience. "
        "If a project is exceptionally strong or directly relevant to the company's domain "
        "(e.g., a financial tracker project when emailing a fintech company), include it as a supplementary highlight. "
        "Create concise bullet points prefixed with `- ` (one per line)\n"
        "- Wrap key metrics and numbers in **double asterisks** (e.g. **$1.6M+**, **83%**, **10k+ sessions**)\n"
        "- Do NOT include LinkedIn/GitHub URLs in the body — they are added separately\n"
        + structure_rules
        + "- Do NOT add content outside the placeholders\n"
        "- Do NOT remove or rearrange any part of the template\n"
        "- Return the completed email body only — no extra formatting or labels\n\n"
        f"--- Template to fill ---\n{pre_filled_template}"
    )

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def _parse_subject_body(raw_text: str) -> Dict[str, str]:
    """
    Parse the LLM response into subject and body using the SUBJECT:/BODY: format.
    """
    subject = ""
    body = raw_text.strip()

    if "SUBJECT:" in raw_text and "BODY:" in raw_text:
        parts = raw_text.split("BODY:", 1)
        subject_part = parts[0]
        body = parts[1].strip()

        subject_line = subject_part.split("SUBJECT:", 1)[1]
        subject = subject_line.strip().split("\n")[0].strip()

    # Fallback: if no format detected, use first sentence as subject
    if not subject and body:
        first_sentence = body.split(".")[0].strip()
        subject = first_sentence[:80] if len(first_sentence) > 10 else "Interested in opportunities at your company"

    return {"subject": subject, "body": body}


# ---------------------------------------------------------------------------
# Main generation entry point
# ---------------------------------------------------------------------------

def get_openai_response(
    scraped_data: Dict[str, Any],
    company_data: Optional[Dict[str, Any]] = None,
    resume_data: Optional[Dict[str, Any]] = None,
    contact_data: Optional[Dict[str, Any]] = None,
    mode: str = "template",
    template: Optional[str] = None,
    subject_template: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    github_url: Optional[str] = None,
    smooth_grammar: bool = True,
) -> Dict[str, str]:
    """
    Generate a personalized cold email using GPT.
    Returns {"subject": str, "body": str}.

    Modes:
        "template" — fill user-provided template with context data (default)
        "ml"       — fully GPT-generated email (locked, not yet available)
    """
    client = get_client()

    # Resolve link URLs once for use in return value and placeholder stripping
    resolved_urls = _resolve_link_urls(resume_data, linkedin_url, github_url)

    if mode == "template" and template:
        # Pass 1: deterministic replacements (strip links — they go in HTML footer)
        pre_filled = _fill_deterministic_placeholders(
            template, company_data, contact_data, resume_data,
            linkedin_url, github_url,
            strip_link_placeholders=True,
        )

        # Pass 2: GPT fills contextual placeholders
        prompt = generate_template_prompt(
            pre_filled, scraped_data, company_data, resume_data, contact_data,
            smooth_grammar=smooth_grammar,
        )
        system_msg = (
            "You fill in email templates by replacing bracketed placeholders "
            "with specific, relevant content. Preserve the template structure exactly."
        )
    else:
        # From-scratch generation (future ML mode foundation)
        prompt = generate_prompt(scraped_data, company_data, resume_data, contact_data)
        system_msg = (
            "You write short, personalized cold outreach emails for software engineers. "
            "Every email must reference specific details about the company and the sender's background. "
            "Never write generic templates."
        )

    response = client.responses.create(
        model="gpt-5-nano",
        input=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
    )

    # Extract text from response
    raw_text = None
    for block in response.output:
        if hasattr(block, "content") and block.content:
            for item in block.content:
                if hasattr(item, "text"):
                    raw_text = item.text
                    break
        if raw_text:
            break

    if not raw_text:
        raise RuntimeError("No text found in OpenAI response.")

    if mode == "template" and template:
        # Template mode: body is the raw GPT output, subject from template or default
        subject = ""
        if subject_template:
            subject = _fill_deterministic_placeholders(
                subject_template, company_data, contact_data, resume_data,
                linkedin_url, github_url,
            )
        else:
            company_name = (company_data or {}).get("name", "your company")
            subject = f"Contributing to {company_name}'s mission"
        return {
            "subject": subject,
            "body": raw_text.strip(),
            **resolved_urls,
        }
    else:
        result = _parse_subject_body(raw_text)
        result.update(resolved_urls)
        return result
