"""
Authentication dependencies.

- verify_jwt: For user-facing endpoints. Validates JWT and returns user email.
- verify_api_key: For machine-to-machine calls (Lambda → backend).
- verify_jwt_or_api_key: Accepts either (used by /send/draft).
"""

import os

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.jwt_manager import decode_token

_bearer_scheme = HTTPBearer()

API_KEY = os.environ.get("API_KEY", "")


async def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """Verify JWT token and return the user's email."""
    try:
        payload = decode_token(credentials.credentials)
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject.",
            )
        return email
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired. Please reconnect Gmail.",
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """Verify shared API key (for Lambda/service calls)."""
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API_KEY not configured.",
        )
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
    return credentials.credentials


async def verify_jwt_or_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    """Accept either a valid JWT (returns email) or a valid API key (returns 'service')."""
    token = credentials.credentials

    # Try JWT first
    try:
        payload = decode_token(token)
        email = payload.get("sub")
        if email:
            return email
    except pyjwt.InvalidTokenError:
        pass

    # Fall back to API key
    if API_KEY and token == API_KEY:
        return "service"

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token or API key.",
    )
