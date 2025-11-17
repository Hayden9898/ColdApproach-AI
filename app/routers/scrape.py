from fastapi import APIRouter
from app.utils.scraper import scrape_company

router = APIRouter(prefix="/scrape", tags=["scrape"])

@router.get("/")
def scrape_url(url: str):
    result = scrape_company(url)
    if result == "Error":
        return {"Error": "Failed to scrape company"}
    else:
        return {"Company Data": result}

