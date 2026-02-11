from fastapi import APIRouter, HTTPException
from app.utils.scraper import scrape_company

router = APIRouter(prefix="/scrape", tags=["scrape"])

@router.get("/")
def scrape_url(url: str):
    """
    Pure company webpage scrape endpoint.
    No OpenAI call is made here.
    """
    result = scrape_company(url)
    if not isinstance(result, dict):
        raise HTTPException(status_code=500, detail="Failed to scrape company.")

    if result.get("error"):
        raise HTTPException(status_code=500, detail=f"Scrape failed: {result['error']}")

    return {
        "success": True,
        "company_data": result,
        "note": "Scrape-only response (no LLM generation).",
    }

