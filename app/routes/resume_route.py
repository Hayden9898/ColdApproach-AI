from typing import Dict

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.utils.resume_parser import extract_resume_text

router = APIRouter()

PDF_MIME_TYPE = "application/pdf"


@router.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)) -> Dict[str, str]:
    """
    Accept a PDF resume upload, extract raw text, and return it as JSON.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed (invalid extension).")

    if file.content_type != PDF_MIME_TYPE:
        raise HTTPException(status_code=400, detail="Invalid Content-Type. Expected application/pdf.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")

    try:
        result = extract_resume_text(file_bytes)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    print(result)  # Temporary logging for manual verification
    return result

