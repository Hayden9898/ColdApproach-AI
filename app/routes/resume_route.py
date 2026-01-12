from typing import Dict

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.utils.resume_parser import extract_resume_text, format_resume, is_resume

router = APIRouter(prefix="/resume", tags=["resume"])

PDF_MIME_TYPE = "application/pdf"


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)) -> Dict:
    """
    Accept a PDF resume upload, extract raw text and structured data.
    Returns session-based profile data (not stored).
    
    Flow:
    1. Extract raw text from PDF
    2. Extract structured data (name, email, skills, experience, etc.)
    3. Return profile for use in current session
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed (invalid extension).")

    if file.content_type != PDF_MIME_TYPE:
        raise HTTPException(status_code=400, detail="Invalid Content-Type. Expected application/pdf.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")

    try:
        # Step 1: Extract raw text
        text_result = extract_resume_text(file_bytes)
        resume_text = text_result.get("text")
        
        # Step 2: Validate that it's actually a resume
        if not is_resume(resume_text):
            raise HTTPException(
                status_code=400,
                detail="File uploaded does not appear to be a resume. Please upload a valid resume PDF."
            )
        
        # Step 3: Format resume into structured data
        structured_data = format_resume(resume_text)
        
        # Return session-based profile
        return {
            "success": True,
            "raw_text": resume_text,  # Keep for debugging/reference
            "profile": {
                **structured_data,
                "resume_text_length": len(resume_text)
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors) as-is
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing resume: {str(exc)}"
        ) from exc

