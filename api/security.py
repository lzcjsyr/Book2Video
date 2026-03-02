"""API security dependencies."""

import os
import secrets
from typing import Optional

from fastapi import Header, HTTPException, status


def verify_api_token(x_api_token: Optional[str] = Header(default=None)) -> None:
    """
    Verify API token if API_TOKEN is configured.

    If API_TOKEN is absent, auth is considered disabled for local development.
    """
    configured_token = os.getenv("API_TOKEN")
    if not configured_token:
        return
    if not x_api_token or not secrets.compare_digest(x_api_token, configured_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
        )

