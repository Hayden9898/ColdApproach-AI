from typing import Any, Dict, Optional


def get_client():
    """
    Lazy-load OpenAI client to avoid crashing app on import when key is missing.
    """
    from openai import OpenAI

    return OpenAI()


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
    url = scraped_data.get("url", "Unknown URL")
    blocked = scraped_data.get("blocked")
    title = scraped_data.get("title")
    description = scraped_data.get("description")
    og_description = scraped_data.get("og_description")
    h1_list = scraped_data.get("h1") or []
    summary_keywords = scraped_data.get("summary_keywords") or []
    error = scraped_data.get("error")

    sections = [f"Company URL: {url}"]

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
            # Cross-reference with company keywords for relevance
            company_kw_lower = {kw.lower() for kw in summary_keywords}
            matching = [s for s in skills if s.lower() in company_kw_lower]
            other = [s for s in skills if s.lower() not in company_kw_lower]
            if matching:
                resume_parts.append(f"Relevant Skills (match company): {', '.join(matching[:10])}")
            if other:
                resume_parts.append(f"Other Skills: {', '.join(other[:10])}")

        experience = resume_data.get("experience") or []
        for i, exp in enumerate(experience[:2]):
            exp_title = exp.get("title", "")
            exp_company = exp.get("company", "")
            exp_duration = exp.get("duration", "")
            bullets = exp.get("description") or []
            exp_str = f"Experience {i+1}: {exp_title} at {exp_company} ({exp_duration})"
            if bullets:
                exp_str += "\n  " + "\n  ".join(bullets[:3])
            resume_parts.append(exp_str)

        education = resume_data.get("education") or []
        for edu in education[:1]:
            edu_str = f"Education: {edu.get('degree', '')} — {edu.get('school', '')}"
            if edu.get("gpa"):
                edu_str += f" (GPA: {edu['gpa']})"
            resume_parts.append(edu_str)

        if resume_parts:
            sections.append("--- Sender Profile (your resume) ---\n" + "\n".join(resume_parts))

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
            "- Connect at least one of the sender's skills or experiences to the company's work\n"
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


def get_openai_response(
    scraped_data: Dict[str, Any],
    company_data: Optional[Dict[str, Any]] = None,
    resume_data: Optional[Dict[str, Any]] = None,
    contact_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Generate a personalized cold email using GPT-5-nano.
    Returns {"subject": str, "body": str}.
    """
    client = get_client()

    prompt = generate_prompt(scraped_data, company_data, resume_data, contact_data)

    response = client.responses.create(
        model="gpt-5-nano",
        input=[
            {
                "role": "system",
                "content": (
                    "You write short, personalized cold outreach emails for software engineers. "
                    "Every email must reference specific details about the company and the sender's background. "
                    "Never write generic templates."
                ),
            },
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

    return _parse_subject_body(raw_text)
