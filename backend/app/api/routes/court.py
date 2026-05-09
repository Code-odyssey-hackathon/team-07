"""
Madhyastha — Court Filing Routes
Petition PDF, evidence bundle, eCourts link
"""
import os
import json
import logging
import zipfile
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.models.models import Dispute, Party, Statement, ArbitrationCase, Agreement
from app.schemas.schemas import CourtFilingResponse
from app.services.pdf_service import generate_petition_pdf

logger = logging.getLogger("madhyastha.api.court")
router = APIRouter(prefix="/court", tags=["Court Filing"])

EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "evidence")


@router.get("/{dispute_id}/petition")
async def get_petition(dispute_id: str, db: Session = Depends(get_db)):
    """Generate pre-filled petition PDF"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    pdf_path = generate_petition_pdf(
        {"title": dispute.title, "dispute_type": dispute.dispute_type,
         "id": dispute.id, "status": dispute.status},
        f"petition_{dispute_id}.pdf"
    )
    return FileResponse(pdf_path, media_type="application/pdf",
                       filename=f"petition_{dispute_id}.pdf")


@router.get("/{dispute_id}/evidence-bundle")
async def get_evidence_bundle(dispute_id: str, db: Session = Depends(get_db)):
    """Download complete evidence trail as ZIP"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    zip_path = os.path.join(EVIDENCE_DIR, f"evidence_{dispute_id}.zip")

    with zipfile.ZipFile(zip_path, "w") as zf:
        # Add statements
        stmts = db.query(Statement).filter(Statement.dispute_id == dispute_id).all()
        for s in stmts:
            content = json.dumps({
                "party_id": s.party_id, "position": s.position,
                "interest": s.interest, "min_acceptable": s.min_acceptable,
                "emotional_need": s.emotional_need
            }, indent=2)
            zf.writestr(f"statement_{s.party_id[:8]}.json", content)

        # Add agreements
        agreements = db.query(Agreement).filter(Agreement.dispute_id == dispute_id).all()
        for a in agreements:
            if a.pdf_path and os.path.exists(a.pdf_path):
                zf.write(a.pdf_path, os.path.basename(a.pdf_path))

        # Add arbitration briefs/awards
        arb = db.query(ArbitrationCase).filter(ArbitrationCase.dispute_id == dispute_id).first()
        if arb:
            if arb.ai_brief_pdf_path and os.path.exists(arb.ai_brief_pdf_path):
                zf.write(arb.ai_brief_pdf_path, "arbitration_brief.pdf")
            if arb.award_pdf_path and os.path.exists(arb.award_pdf_path):
                zf.write(arb.award_pdf_path, "arbitration_award.pdf")

        # Add dispute summary
        summary = json.dumps({
            "dispute_id": dispute.id, "title": dispute.title,
            "type": dispute.dispute_type, "status": dispute.status,
            "created": dispute.created_at.isoformat() if dispute.created_at else None
        }, indent=2)
        zf.writestr("dispute_summary.json", summary)

    return FileResponse(zip_path, media_type="application/zip",
                       filename=f"evidence_{dispute_id}.zip")


@router.get("/{dispute_id}/ecourts-link")
async def get_ecourts_link(dispute_id: str):
    """Get eCourts filing portal link"""
    return CourtFilingResponse(
        dispute_id=dispute_id, petition_available=True,
        evidence_bundle_available=True,
        ecourts_link="https://efiling.ecourts.gov.in/",
        message="Download the petition and evidence bundle, then file on eCourts portal."
    )
