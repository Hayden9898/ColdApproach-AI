import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.routers import scrape, send, analytics, contacts, resume, auth, batch
from app.services.batch_worker import start_worker, stop_worker
from app.utils.auth import verify_api_key

CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: launch the background SQS worker
    start_worker()
    yield
    # Shutdown: signal the worker to stop
    stop_worker()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Protected routers — require bearer token
_auth = [Depends(verify_api_key)]
app.include_router(scrape.router, dependencies=_auth)
app.include_router(send.router, dependencies=_auth)
app.include_router(analytics.router, dependencies=_auth)
app.include_router(contacts.router, dependencies=_auth)
app.include_router(resume.router, dependencies=_auth)
app.include_router(batch.router, dependencies=_auth)

# Auth router — selective protection (login/callback are open, status endpoints are protected)
app.include_router(auth.router)


@app.get("/")
def root():
    return {"message": "ColdReach API running"}
