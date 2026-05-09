"""
Madhyastha — Arbitration Routes
Full arbitration management: scheduling, awards, downloads
"""
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.models.models import Dispute, ArbitrationCase, Arbitrator, Agreement, generate_uuid
from app.schemas.schemas import (ArbitrationCaseResponse, HearingScheduleRequest,
                                  AwardSubmitRequest, MessageResponse)
from app.services.pdf_service import generate_award_pdf
from app.services.notification_service import notify_parties
from app.models.models import Party

logger = logging.getLogger("madhyastha.api.arbitration")
router = APIRouter(prefix="/arbitration", tags=["Arbitration"])


@router.get("/{case_id}", response_model=ArbitrationCaseResponse)
async def get_arbitration_case(case_id: str, db: Session = Depends(get_db)):
    """Get arbitration case details"""
    arb = db.query(ArbitrationCase).filter(ArbitrationCase.id == case_id).first()
    if not arb:
        arb = db.query(ArbitrationCase).filter(ArbitrationCase.dispute_id == case_id).first()
    if not arb:
        raise HTTPException(status_code=404, detail="Arbitration case not found")

    arbitrator = db.query(Arbitrator).filter(Arbitrator.id == arb.arbitrator_id).first() if arb.arbitrator_id else None
    return ArbitrationCaseResponse(
        id=arb.id, dispute_id=arb.dispute_id, arbitrator_id=arb.arbitrator_id,
        arbitrator_name=arbitrator.name if arbitrator else None,
        status=arb.status, consent_a=arb.consent_a, consent_b=arb.consent_b,
        hearing_datetime=arb.hearing_datetime, hearing_link=arb.hearing_link,
        award=arb.award, created_at=arb.created_at
    )


@router.post("/{case_id}/schedule", response_model=MessageResponse)
async def schedule_hearing(case_id: str, data: HearingScheduleRequest, db: Session = Depends(get_db)):
    """Arbitrator schedules a hearing"""
    arb = db.query(ArbitrationCase).filter(ArbitrationCase.id == case_id).first()
    if not arb:
        raise HTTPException(status_code=404, detail="Case not found")

    arb.hearing_datetime = data.hearing_datetime
    arb.hearing_link = data.hearing_link
    arb.status = "hearing_scheduled"

    dispute = db.query(Dispute).filter(Dispute.id == arb.dispute_id).first()
    if dispute:
        dispute.status = "arbitration_hearing"

    db.commit()
    return MessageResponse(message="Hearing scheduled successfully")


@router.post("/{case_id}/award", response_model=MessageResponse)
async def submit_award(case_id: str, data: AwardSubmitRequest, db: Session = Depends(get_db)):
    """Arbitrator submits the award"""
    arb = db.query(ArbitrationCase).filter(ArbitrationCase.id == case_id).first()
    if not arb:
        raise HTTPException(status_code=404, detail="Case not found")

    award_data = data.model_dump()
    arb.award = award_data
    arb.status = "award_issued"
    arb.issued_at = datetime.now(timezone.utc)

    pdf_path = generate_award_pdf(award_data, f"award_{arb.dispute_id}.pdf")
    arb.award_pdf_path = pdf_path

    dispute = db.query(Dispute).filter(Dispute.id == arb.dispute_id).first()
    if dispute:
        dispute.status = "award_issued"

    # Create agreement record for the award
    agreement = Agreement(
        id=generate_uuid(), dispute_id=arb.dispute_id,
        agreement_type="arbitration_award", terms=award_data, pdf_path=pdf_path
    )
    db.add(agreement)
    db.commit()
    return MessageResponse(message="Award issued successfully")


@router.get("/{case_id}/award/download")
async def download_award(case_id: str, db: Session = Depends(get_db)):
    """Download award PDF"""
    arb = db.query(ArbitrationCase).filter(ArbitrationCase.id == case_id).first()
    if not arb:
        arb = db.query(ArbitrationCase).filter(ArbitrationCase.dispute_id == case_id).first()
    if not arb or not arb.award_pdf_path:
        raise HTTPException(status_code=404, detail="Award PDF not found")
    import os
    if not os.path.exists(arb.award_pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    return FileResponse(arb.award_pdf_path, media_type="application/pdf")


@router.get("/{case_id}/brief/download")
async def download_brief(case_id: str, db: Session = Depends(get_db)):
    """Download AI-prepared brief PDF"""
    arb = db.query(ArbitrationCase).filter(ArbitrationCase.id == case_id).first()
    if not arb:
        arb = db.query(ArbitrationCase).filter(ArbitrationCase.dispute_id == case_id).first()
    if not arb or not arb.ai_brief_pdf_path:
        raise HTTPException(status_code=404, detail="Brief PDF not found")
    import os
    if not os.path.exists(arb.ai_brief_pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    return FileResponse(arb.ai_brief_pdf_path, media_type="application/pdf")
