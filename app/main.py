from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.routers import scrape, send, analytics, contacts, resume, auth, batch
from app.services.batch_worker import start_worker, stop_worker


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
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scrape.router)
app.include_router(send.router)
app.include_router(analytics.router)
app.include_router(contacts.router)
app.include_router(resume.router)
app.include_router(auth.router)
app.include_router(batch.router)


@app.get("/")
def root():
    return {"message": "ColdReach API running"}
