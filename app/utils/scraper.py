from bs4 import BeautifulSoup
import requests
import logging
import re

def get_text_or_none(el):
    return el.get_text(strip=True) if el else None

def get_list_text(els):
    return [el.get_text(strip=True) for el in els if el.get_text(strip=True)]

# --------- Extract simple high-value keywords from body ---------
import re

SHORT_KEYWORDS = {
    "ai","ml","llm","nlp","cv","dl","rl","gpt",
    "ar","vr","xr",
    "api","sdk","cli","dev","ops","ci","cd","git","k8s",
    "aws","gcp","azure","sql","db","gpu","cpu","vm",
    "etl","bi","rt",
    "iam","ssl","tls","vpn",
    "ux","ui","qa","pm",
    "iot","ble","rf","pcb","usb"
}

STOPWORDS = {
    "the","and","for","with","this","that","from","are","was","our","your",
    "but","you","they","their","them","all","any","can","more","about","into",
    "over","also","how","why","what","when","where","who","use","used","using",
    "on","in","at","of","to","as","is","it","be","or","by","we","an","a","so","do"
}

def extract_keywords(text: str, limit: int = 25):
    text = text.lower()
    text = re.sub(r"[^a-z ]+", " ", text)
    words = text.split()

    clean = []
    for w in words:
        if w in SHORT_KEYWORDS:
            clean.append(w)
        elif w not in STOPWORDS and len(w) > 3:
            clean.append(w)

    freq = {}
    for w in clean:
        freq[w] = freq.get(w, 0) + 1

    sorted_words = sorted(freq, key=freq.get, reverse=True)
    return sorted_words[:limit]



# --------------------------------------------------------
# MAIN SCRAPER
# --------------------------------------------------------
def scrape_company(url: str):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # ---------- Title ----------
        title_tag = soup.find("title")
        title_text = get_text_or_none(title_tag)

        # Blocked check
        if title_text and "blocked" in title_text.lower():
            return {
                "url": url,
                "blocked": True,
                "title": title_text,
                "description": None,
                "og_description": None,
                "h1": [],
                "summary_keywords": []
            }

        # ---------- Meta description ----------
        meta_desc = soup.find("meta", attrs={"name": "description"})
        description = meta_desc["content"] if meta_desc and meta_desc.get("content") else None

        # ---------- OG description ----------
        og_desc = soup.find("meta", property="og:description")
        og_description = og_desc["content"] if og_desc and og_desc.get("content") else None

        # ---------- H1 Headings ----------
        h1_list = get_list_text(soup.find_all("h1"))[:4]

        # ---------- Extract High-Value Keywords (mini summary) ----------
        full_text = soup.get_text(" ", strip=True)
        summary_keywords = extract_keywords(full_text, limit=40)

        # ---------- Return clean data ----------
        return {
            "url": url,
            "blocked": False,
            "title": title_text,
            "description": description,
            "og_description": og_description,
            "h1": h1_list,
            "summary_keywords": summary_keywords
        }

    except Exception as e:
        logging.error(f"Error scraping company: {e}")
        return {"error": str(e)}
