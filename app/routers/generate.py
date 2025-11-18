from typing import Any, Dict
from openai import OpenAI


#Note: This currently generates a general template, TODO implement resume parsing first for a more personalized approach.
client = OpenAI()


def generate_prompt(scraped_data: Dict[str, Any]) -> str:
    """
    Build a structured prompt from the scraped company data returned by scrape_company().
    """

    url = scraped_data.get("url", "Unknown URL")
    blocked = scraped_data.get("blocked")
    title = scraped_data.get("title")
    description = scraped_data.get("description")
    og_description = scraped_data.get("og_description")
    h1_list = scraped_data.get("h1") or []
    summary_keywords = scraped_data.get("summary_keywords") or []
    error = scraped_data.get("error")

    sections = [
        "You are an expert email writer. Create ONLY the body of a short, personalized outreach email to this company about potential opportunities in software engineering/development.",
        f"Scraped URL: {url}",
    ]

    if blocked is True:
        sections.append(
            "The website returned a blocking or anti-bot page. Infer the company’s focus using the metadata below."
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

    sections.append(
        "Write ONLY the body (no greeting, no signature, no subject line). "
        "The email should:\n"
        "- Be 4–6 sentences (under 120 words)\n"
        "- Start directly with a relevant insight about the company\n"
        "- Sound personal and natural, not generic\n"
        "- Avoid buzzwords and hype\n"
        "- End with a soft CTA asking for a quick chat\n"
        "Return only the body paragraph text."
    )

    return "\n\n".join(sections)


def get_openai_response(scraped_data: Dict[str, Any]) -> str:
    """
    Call GPT-5-nano using the Responses API and return the generated email body.
    """
    prompt = generate_prompt(scraped_data)

    response = client.responses.create(
        model="gpt-5-nano",
        input=[
            {
                "role": "system",
                "content": "You write clean, natural, personalized B2B cold outreach email bodies."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    # Safe text extraction across all response structures
    for block in response.output:
        if hasattr(block, "content"):
            for item in block.content:
                if hasattr(item, "text"):
                    return item.text

    raise RuntimeError("No valid text found in OpenAI response.")
