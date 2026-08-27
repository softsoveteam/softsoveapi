from __future__ import annotations

import secrets
from typing import Optional, Set

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

_tokens: Set[str] = set()
_bearer = HTTPBearer(auto_error=False)


def create_token() -> str:
    token = secrets.token_urlsafe(32)
    _tokens.add(token)
    return token


def require_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin login required.")
    if credentials.credentials not in _tokens:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired admin token.")
    return credentials.credentials


def password_ok(password: str) -> bool:
    return secrets.compare_digest(password, settings.admin_password)
