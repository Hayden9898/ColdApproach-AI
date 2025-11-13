from fastapi import FastAPI  # type: ignore[import-not-found]

app = FastAPI()

@app.get("/")
def root():
    return {"message": "ColdReach API running"}
