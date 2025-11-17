from fastapi import APIRouter

router = APIRouter(prefix="/send", tags=["send"])

@router.get("/")
def send_placeholder():
    pass

