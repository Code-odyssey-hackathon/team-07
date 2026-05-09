"""
Madhyastha — Dispute Routes
Registration, status, listing, and stats
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.dependencies import get_db
from app.core.security import create_party_token
from app.core.config import settings
from app.models.models import Dispute, Party, generate_uuid, DISPUTE_TYPES
from app.schemas.schemas import (
    DisputeRegister, DisputeResponse, DisputeRegistrationResult,
    DisputeStatusResponse, StatsSummary, MessageResponse
)
from app.services.notification_service import send_dispute_link

logger = logging.getLogger("madhyastha.api.dispute")
router = APIRouter(prefix="/dispute", tags=["Dispute Management"])


@router.post("/register", response_model=DisputeRegistrationResult)
async def register_dispute(data: DisputeRegister, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Register a new dispute and generate party session tokens"""
    if data.dispute_type not in DISPUTE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid dispute type. Must be one of: {DISPUTE_TYPES}")

    dispute_id = generate_uuid()
    dispute = Dispute(
        id=dispute_id, title=data.title, description=data.description,
        dispute_type=data.dispute_type, status="registered",
        arbitration_consent=data.arbitration_consent
    )
    db.add(dispute)

    party_a_id = generate_uuid()
    party_a = Party(
        id=party_a_id, dispute_id=dispute_id, role="party_a",
        name=data.party_a.name, phone=data.party_a.phone,
        email=data.party_a.email, language=data.party_a.language,
        arbitration_consent=data.arbitration_consent
    )
    party_a.session_token = create_party_token(party_a_id, dispute_id, "party_a")
    db.add(party_a)

    party_b_id = generate_uuid()
    party_b = Party(
        id=party_b_id, dispute_id=dispute_id, role="party_b",
        name=data.party_b.name, phone=data.party_b.phone,
        email=data.party_b.email, language=data.party_b.language,
        arbitration_consent=data.arbitration_consent
    )
    party_b.session_token = create_party_token(party_b_id, dispute_id, "party_b")
    db.add(party_b)

    dispute.status = "awaiting_party_b"
    db.commit()
    db.refresh(dispute)

    frontend_url = settings.FRONTEND_URL
    party_a_link = f"{frontend_url}/caucus?token={party_a.session_token}"
    party_b_link = f"{frontend_url}/caucus?token={party_b.session_token}"

    # Send email notifications in background (non-blocking)
    if data.party_a.email:
        background_tasks.add_task(
            send_dispute_link, data.party_a.name, data.party_a.email,
            "party_a", party_a_link, data.title
        )
    if data.party_b.email:
        background_tasks.add_task(
            send_dispute_link, data.party_b.name, data.party_b.email,
            "party_b", party_b_link, data.title
        )

    return DisputeRegistrationResult(
        dispute=DisputeResponse.model_validate(dispute),
        party_a_token=party_a.session_token,
        party_b_token=party_b.session_token,
        party_a_link=party_a_link,
        party_b_link=party_b_link,
        message="Dispute registered successfully. Session links have been emailed to both parties."
    )


@router.get("/{dispute_id}/status", response_model=DisputeStatusResponse)
async def get_dispute_status(dispute_id: str, db: Session = Depends(get_db)):
    """Get current dispute status"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return DisputeStatusResponse.model_validate(dispute)


@router.get("/all", response_model=List[DisputeResponse])
async def list_all_disputes(db: Session = Depends(get_db)):
    """List all disputes (admin endpoint)"""
    disputes = db.query(Dispute).order_by(Dispute.created_at.desc()).all()
    return [DisputeResponse.model_validate(d) for d in disputes]


@router.get("/stats/summary", response_model=StatsSummary)
async def get_stats_summary(db: Session = Depends(get_db)):
    """Get resolution statistics summary"""
    total = db.query(Dispute).count()
    resolved = db.query(Dispute).filter(Dispute.status.in_(["resolved", "closed"])).count()
    escalated = db.query(Dispute).filter(Dispute.status.in_(
        ["escalated_arbitration", "arbitration_hearing", "award_issued"])).count()
    court = db.query(Dispute).filter(Dispute.status == "court_filing").count()
    active = total - resolved - court

    by_type = {}
    for dt in DISPUTE_TYPES:
        c = db.query(Dispute).filter(Dispute.dispute_type == dt).count()
        if c > 0:
            by_type[dt] = c

    by_status = {}
    for row in db.query(Dispute.status, func.count(Dispute.id)).group_by(Dispute.status).all():
        by_status[row[0]] = row[1]

    return StatsSummary(
        total_disputes=total, active_disputes=active, resolved_disputes=resolved,
        escalated_to_arbitration=escalated, court_filings=court,
        resolution_rate=round((resolved / total * 100) if total > 0 else 0, 1),
        disputes_by_type=by_type, disputes_by_status=by_status
    )
