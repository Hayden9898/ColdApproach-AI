from fastapi import FastAPI

from app.routers import scrape, generate, send, analytics

app = FastAPI()

app.include_router(scrape.router)
app.include_router(generate.router)
app.include_router(send.router)
app.include_router(analytics.router)

@app.get("/")
def root():
    return {"message": "ColdReach API running"}
