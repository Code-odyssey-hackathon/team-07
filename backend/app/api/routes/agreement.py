"""
Madhyastha — Agreement Routes
Agreement generation, viewing, signing, and PDF download
"""
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_party
from app.models.models import Dispute, Party, Agreement, generate_uuid
from app.schemas.schemas import AgreementResponse, SignatureRequest, MessageResponse
from app.agents.agreement_drafter import AgreementDrafter
from app.services.pdf_service import generate_agreement_pdf
from app.services.notification_service import send_agreement_notification

logger = logging.getLogger("madhyastha.api.agreement")
router = APIRouter(prefix="/agreement", tags=["Agreement"])


@router.post("/{dispute_id}/generate", response_model=AgreementResponse)
async def generate_agreement(dispute_id: str, db: Session = Depends(get_db)):
    """Generate agreement after parties reach consensus"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if dispute.status != "agreement_pending":
        raise HTTPException(status_code=400, detail="Dispute not in agreement_pending status")

    parties = db.query(Party).filter(Party.dispute_id == dispute_id).all()
    pa = next((p for p in parties if p.role == "party_a"), None)
    pb = next((p for p in parties if p.role == "party_b"), None)
    if not pa or not pb:
        raise HTTPException(status_code=400, detail="Both parties required")

    agreed_option = dispute.final_terms or {}
    options = dispute.settlement_options or []
    option_id = agreed_option.get("agreed_option", "B")
    selected = next((o for o in options if o.get("option_id") == option_id), options[0] if options else {})

    drafter = AgreementDrafter()
    terms = await drafter.draft(
        {"title": dispute.title, "dispute_type": dispute.dispute_type},
        {"name": pa.name, "email": pa.email, "phone": pa.phone},
        {"name": pb.name, "email": pb.email, "phone": pb.phone},
        {"option": selected, "terms": selected.get("terms", "As negotiated")}
    )

    pdf_path = generate_agreement_pdf(terms, f"agreement_{dispute_id}.pdf")

    agreement = Agreement(
        id=generate_uuid(), dispute_id=dispute_id, agreement_type="mediation_settlement",
        terms=terms, pdf_path=pdf_path
    )
    db.add(agreement)
    db.commit()
    db.refresh(agreement)
    return AgreementResponse.model_validate(agreement)


@router.get("/{dispute_id}", response_model=AgreementResponse)
async def get_agreement(dispute_id: str, db: Session = Depends(get_db)):
    """Get agreement details"""
    agreement = db.query(Agreement).filter(Agreement.dispute_id == dispute_id).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")
    return AgreementResponse.model_validate(agreement)


@router.post("/{dispute_id}/sign", response_model=MessageResponse)
async def sign_agreement(
    dispute_id: str, data: SignatureRequest,
    background_tasks: BackgroundTasks,
    party_info: dict = Depends(get_current_party),
    db: Session = Depends(get_db)
):
    """Submit digital signature for the agreement"""
    agreement = db.query(Agreement).filter(Agreement.dispute_id == dispute_id).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")

    party = party_info["party"]
    now = datetime.now(timezone.utc)

    if party.role == "party_a":
        agreement.party_a_signed = True
        agreement.party_a_signed_at = now
    else:
        agreement.party_b_signed = True
        agreement.party_b_signed_at = now

    party.has_signed_agreement = True

    # Check if fully signed: for arbitration awards, need arbitrator signature too
    finalized = False
    if agreement.party_a_signed and agreement.party_b_signed:
        if agreement.agreement_type == "arbitration_award" and not agreement.arbitrator_signed:
            pass  # Wait for arbitrator to also sign
        else:
            agreement.finalized_at = now
            dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
            if dispute:
                dispute.status = "resolved"
            finalized = True

    db.commit()

    # Send finalized agreement emails with PDF to both parties
    if finalized:
        parties = db.query(Party).filter(Party.dispute_id == dispute_id).all()
        dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
        for p in parties:
            if p.email:
                background_tasks.add_task(
                    send_agreement_notification, p.name, p.email,
                    dispute.title if dispute else "Dispute", agreement.pdf_path
                )

    return MessageResponse(message=f"Signature recorded for {party.name}", success=True)


@router.post("/{dispute_id}/arbitrator-sign")
async def arbitrator_sign_agreement(
    dispute_id: str, token: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Arbitrator digitally signs the agreement"""
    from app.api.routes.arbitrator_auth import verify_arbitrator_token
    from app.models.models import Arbitrator

    payload = verify_arbitrator_token(token)
    arb = db.query(Arbitrator).filter(Arbitrator.id == payload["sub"]).first()
    if not arb:
        raise HTTPException(status_code=404, detail="Arbitrator not found")

    agreement = db.query(Agreement).filter(Agreement.dispute_id == dispute_id).first()
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")

    now = datetime.now(timezone.utc)
    agreement.arbitrator_signed = True
    agreement.arbitrator_signed_at = now
    agreement.arbitrator_name = arb.name

    # Check if all signatures are complete
    finalized = False
    if agreement.party_a_signed and agreement.party_b_signed and agreement.arbitrator_signed:
        agreement.finalized_at = now
        dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
        if dispute:
            dispute.status = "resolved"
        finalized = True

    db.commit()
    logger.info(f"Arbitrator {arb.name} signed agreement for dispute {dispute_id}")

    # Send finalized agreement emails with PDF to both parties
    if finalized:
        parties = db.query(Party).filter(Party.dispute_id == dispute_id).all()
        dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
        for p in parties:
            if p.email:
                background_tasks.add_task(
                    send_agreement_notification, p.name, p.email,
                    dispute.title if dispute else "Dispute", agreement.pdf_path
                )

    return {"message": f"Arbitrator {arb.name} has signed the agreement", "success": True}


@router.get("/{dispute_id}/download")
async def download_agreement(dispute_id: str, db: Session = Depends(get_db)):
    """Download signed agreement PDF"""
    agreement = db.query(Agreement).filter(Agreement.dispute_id == dispute_id).first()
    if not agreement or not agreement.pdf_path:
        raise HTTPException(status_code=404, detail="Agreement PDF not found")
    import os
    if not os.path.exists(agreement.pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
    return FileResponse(agreement.pdf_path, media_type="application/pdf",
                       filename=f"agreement_{dispute_id}.pdf")
