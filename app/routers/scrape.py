from fastapi import APIRouter

from app.utils.generate import generate_prompt, get_openai_response
from app.utils.scraper import scrape_company

router = APIRouter(prefix="/scrape", tags=["scrape"])

@router.get("/")
def scrape_url(url: str):
    result = scrape_company(url)
    if result == "Error":
        return {"Error": "Failed to scrape company"}
    if result["blocked"] == True:
        #Use another method to scrape
        pass
    else:
        prompt = generate_prompt(result)
        response = get_openai_response(result)
        print(response)

        return {"Company Data": result, "prompt": prompt, "email_body": response}


