import io
from typing import Dict

import pdfplumber


def extract_resume_text(file_bytes: bytes) -> Dict[str, str]:
    """
    Extract raw text from a PDF resume.

    Raises:
        RuntimeError: If the PDF cannot be read or contains no text.
    """
    if not file_bytes:
        raise RuntimeError("Uploaded PDF is empty.")

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text_parts = []
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(page_text.strip())

        extracted_text = "\n\n".join(text_parts).strip()
    except Exception as exc:  # pragma: no cover - library-specific failures
        raise RuntimeError("Unable to read PDF. Please upload a valid document.") from exc

    if not extracted_text:
        raise RuntimeError("No readable text found in the PDF.")

    return {"text": extracted_text}