from fastapi import FastAPI

from app.routers import scrape, send, analytics, contacts, resume, auth
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.include_router(scrape.router)
app.include_router(send.router)
app.include_router(analytics.router)
app.include_router(contacts.router)
app.include_router(resume.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "ColdReach API running"}
