from fastapi import FastAPI

from app.routers import scrape, send, analytics
from app.routes import resume_route
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.include_router(scrape.router)
app.include_router(send.router)
app.include_router(analytics.router)
app.include_router(resume_route.router)

@app.get("/")
def root():
    return {"message": "ColdReach API running"}
