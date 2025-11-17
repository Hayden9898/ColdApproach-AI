from fastapi import APIRouter

router = APIRouter(prefix="/scrape", tags=["scrape"])

@router.get("/")
def scrape_placeholder():
    pass

