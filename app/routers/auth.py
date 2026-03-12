"""
OAuth2 authentication endpoints.
Currently supports Gmail; extensible for Outlook/Microsoft.
"""

import os
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.utils.auth import verify_jwt
from app.utils.jwt_manager import create_token
from app.utils.token_store import get_token, save_token

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get(
    "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/gmail/callback"
)
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

SCOPES = (
    "https://www.googleapis.com/auth/gmail.compose "
    "https://www.googleapis.com/auth/userinfo.email"
)


@router.get("/gmail/login")
def gmail_login():
    """Redirect user to Google OAuth2 consent screen."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID not configured.")

    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={SCOPES}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    return RedirectResponse(url=auth_url)


@router.get("/gmail/callback")
def gmail_callback(code: str = Query(...), error: str = Query(None)):
    """
    Handle Google OAuth2 callback.
    Exchange authorization code for access + refresh tokens, store keyed by email.
    Returns a JWT to the frontend via redirect query param.
    """
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    import requests as http_requests

    # Exchange code for tokens
    token_response = http_requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Token exchange failed: {token_response.text}",
        )

    token_data = token_response.json()

    # Get user email from Google userinfo
    userinfo_response = http_requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
        timeout=10,
    )

    if userinfo_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve user email.")

    user_email = userinfo_response.json().get("email")
    if not user_email:
        raise HTTPException(status_code=400, detail="No email in userinfo response.")

    save_token(user_email, {
        "access_token": token_data["access_token"],
        "refresh_token": token_data.get("refresh_token"),
        "provider": "gmail",
    })

    # Generate JWT for this user
    user_jwt = create_token(user_email)

    params = urlencode({"jwt": user_jwt, "email": user_email})
    return RedirectResponse(url=f"{FRONTEND_URL}/auth/callback?{params}")


@router.get("/gmail/status", dependencies=[Depends(verify_jwt)])
def gmail_status(email: str = Depends(verify_jwt)):
    """Check if the authenticated user has a valid OAuth token."""
    token = get_token(email)
    if token:
        return {"authenticated": True, "email": email, "provider": "gmail"}
    return {
        "authenticated": False,
        "email": email,
        "detail": "No token found. Complete /auth/gmail/login first.",
    }
