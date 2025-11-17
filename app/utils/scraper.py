from bs4 import BeautifulSoup
import requests
import logging
import json

def get_text_or_none(el):
    return el.get_text(strip=True) if el else None

def get_list_text(els):
    return [el.get_text(strip=True) for el in els if el.get_text(strip=True)]

def scrape_company(url: str):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title
        title_tag = soup.find("title")
        title_text = get_text_or_none(title_tag)

        # Check if blocked early
        blocked = False
        if title_text and "blocked" in title_text.lower():
            blocked = True
            return {
                "url": url,
                "blocked": True,
                "title": title_text,
                "description": None,
                "og_description": None,
                "h1": [],
                "h2": [],
                "nav": [],
                "summary_text": None,
                "schema_org": []
            }

        # Extract meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        description = meta_desc["content"] if meta_desc and meta_desc.get("content") else None

        # Extract OpenGraph description
        og_desc = soup.find("meta", property="og:description")
        og_description = og_desc["content"] if og_desc and og_desc.get("content") else None

        # Extract headings
        h1_list = get_list_text(soup.find_all("h1"))
        h2_list = get_list_text(soup.find_all("h2"))

        # Navigation links
        nav_links = []
        for link in soup.find_all("a"):
            text = link.get_text(strip=True)
            if text and 2 <= len(text) <= 30:
                nav_links.append(text)

        # Summary text
        full_text = soup.get_text(" ", strip=True)
        summary_text = full_text[:400] if full_text else None

        # Schema.org JSON-LD
        schema_list = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                schema_list.append(json.loads(script.string))
            except:
                pass

        return {
            "url": url,
            "blocked": False,
            "title": title_text,
            "description": description,
            "og_description": og_description,
            "h1": h1_list,
            "h2": h2_list,
            "nav": nav_links,
            "summary_text": summary_text,
            "schema_org": schema_list
        }

    except Exception as e:
        logging.error(f"Error scraping company: {e}")
        return {"error": str(e)}
