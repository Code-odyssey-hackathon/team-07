"""
Madhyastha — FastAPI Dependencies
DB session injection, current party authentication
"""

from typing import Generator
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.core.security import verify_party_token, verify_admin_token
from app.models.models import Party


def get_db() -> Generator:
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_party(
    authorization: str = Header(..., description="Bearer <token>"),
    db: Session = Depends(get_db),
) -> dict:
    """Extract and validate party from JWT token in Authorization header"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use: Bearer <token>",
        )

    token = authorization.split(" ", 1)[1]
    token_data = verify_party_token(token)

    # Verify party exists in DB
    party = db.query(Party).filter(Party.id == token_data["party_id"]).first()
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Party not found",
        )

    return {
        "party_id": token_data["party_id"],
        "dispute_id": token_data["dispute_id"],
        "role": token_data["role"],
        "party": party,
    }


async def get_current_admin(
    authorization: str = Header(..., description="Bearer <admin_token>"),
) -> dict:
    """Validate admin token"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    token = authorization.split(" ", 1)[1]
    return verify_admin_token(token)
