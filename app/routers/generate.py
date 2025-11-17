from fastapi import APIRouter

router = APIRouter(prefix="/generate", tags=["generate"])

@router.get("/")
def generate_placeholder():
    pass

