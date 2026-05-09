"""
Madhyastha — JWT Security
Token creation and verification for party session isolation
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
from app.core.config import settings


def create_party_token(party_id: str, dispute_id: str, role: str) -> str:
    """Create a JWT token for a party's session"""
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": party_id,
        "dispute_id": dispute_id,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_party_token(token: str) -> dict:
    """Verify and decode a party's JWT token"""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        party_id = payload.get("sub")
        dispute_id = payload.get("dispute_id")
        role = payload.get("role")

        if not party_id or not dispute_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )

        return {
            "party_id": party_id,
            "dispute_id": dispute_id,
            "role": role,
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def create_admin_token(admin_id: str = "admin") -> str:
    """Create an admin JWT token"""
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": admin_id,
        "role": "admin",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_admin_token(token: str) -> dict:
    """Verify admin token"""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired admin token",
        )
