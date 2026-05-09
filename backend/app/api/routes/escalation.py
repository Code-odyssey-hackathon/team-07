"""
Madhyastha — Escalation Routes
3-stage escalation chain: AI Mediation → Arbitration → Court Filing
"""
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_party
from app.models.models import (Dispute, Party, Statement, ArbitrationCase, Arbitrator,
                                MediationSession, generate_uuid)
from app.schemas.schemas import ArbitrationCaseResponse, ArbitrationConsentRequest, MessageResponse
from app.agents.arbitration_brief import ArbitrationBriefGenerator
from app.services.pdf_service import generate_brief_pdf
from app.rag.retriever import retriever

logger = logging.getLogger("madhyastha.api.escalation")
router = APIRouter(prefix="/escalate", tags=["Escalation"])


@router.post("/{dispute_id}/arbitration", response_model=ArbitrationCaseResponse)
async def escalate_to_arbitration(dispute_id: str, db: Session = Depends(get_db)):
    """Escalate from AI mediation to binding arbitration (requires both party consent)"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    existing = db.query(ArbitrationCase).filter(ArbitrationCase.dispute_id == dispute_id).first()
    if existing:
        return ArbitrationCaseResponse(
            id=existing.id, dispute_id=existing.dispute_id,
            arbitrator_id=existing.arbitrator_id, status=existing.status,
            consent_a=existing.consent_a, consent_b=existing.consent_b,
            created_at=existing.created_at
        )

    # Auto-assign arbitrator
    parties = db.query(Party).filter(Party.dispute_id == dispute_id).all()
    languages = list(set(p.language for p in parties))
    arbitrator = db.query(Arbitrator).filter(
        Arbitrator.available == True
    ).order_by(Arbitrator.cases_assigned.asc()).first()

    arb_case = ArbitrationCase(
        id=generate_uuid(), dispute_id=dispute_id,
        arbitrator_id=arbitrator.id if arbitrator else None,
        status="pending_consent",
        consent_a=dispute.arbitration_consent, consent_b=dispute.arbitration_consent
    )

    if dispute.arbitration_consent:
        arb_case.status = "assigned"
        if arbitrator:
            arbitrator.cases_assigned += 1

    # Generate AI brief
    stmts = db.query(Statement).filter(Statement.dispute_id == dispute_id).all()
    stmt_a = next((s for s in stmts if s.party.role == "party_a"), None)
    stmt_b = next((s for s in stmts if s.party.role == "party_b"), None)
    pa = next((p for p in parties if p.role == "party_a"), None)
    pb = next((p for p in parties if p.role == "party_b"), None)

    if stmt_a and stmt_b and pa and pb:
        precedents = retriever.get_precedents(dispute.title, top_k=3)
        session = db.query(MediationSession).filter(
            MediationSession.dispute_id == dispute_id).first()
        mediation_summary = "AI mediation attempted but parties could not reach agreement."
        if session and session.messages:
            mediation_summary = f"Mediation session had {len(session.messages)} messages."

        brief_gen = ArbitrationBriefGenerator()
        brief = await brief_gen.generate(
            {"title": dispute.title, "dispute_type": dispute.dispute_type},
            {"name": pa.name}, {"name": pb.name},
            {"position": stmt_a.position, "interest": stmt_a.interest, "min_acceptable": stmt_a.min_acceptable},
            {"position": stmt_b.position, "interest": stmt_b.interest, "min_acceptable": stmt_b.min_acceptable},
            mediation_summary, dispute.escalation_reason or "Mediation failed", precedents
        )
        arb_case.ai_brief = json.dumps(brief)
        pdf_path = generate_brief_pdf(brief, f"brief_{dispute_id}.pdf")
        arb_case.ai_brief_pdf_path = pdf_path

    dispute.status = "escalated_arbitration"
    db.add(arb_case)
    db.commit()
    db.refresh(arb_case)

    arb_name = arbitrator.name if arbitrator else None
    return ArbitrationCaseResponse(
        id=arb_case.id, dispute_id=arb_case.dispute_id,
        arbitrator_id=arb_case.arbitrator_id, arbitrator_name=arb_name,
        status=arb_case.status, consent_a=arb_case.consent_a,
        consent_b=arb_case.consent_b, created_at=arb_case.created_at
    )


@router.post("/{dispute_id}/arbitration/consent", response_model=MessageResponse)
async def confirm_consent(
    dispute_id: str, data: ArbitrationConsentRequest,
    party_info: dict = Depends(get_current_party),
    db: Session = Depends(get_db)
):
    """Party confirms arbitration consent"""
    arb_case = db.query(ArbitrationCase).filter(ArbitrationCase.dispute_id == dispute_id).first()
    if not arb_case:
        raise HTTPException(status_code=404, detail="Arbitration case not found")

    party = party_info["party"]
    if party.role == "party_a":
        arb_case.consent_a = data.consent
    else:
        arb_case.consent_b = data.consent

    if arb_case.consent_a and arb_case.consent_b:
        arb_case.status = "assigned"

    db.commit()
    return MessageResponse(message=f"Consent recorded for {party.name}")


@router.get("/arbitration/all")
async def list_arbitration_cases(db: Session = Depends(get_db)):
    """List all arbitration cases (arbitrator dashboard)"""
    cases = db.query(ArbitrationCase).order_by(ArbitrationCase.created_at.desc()).all()
    results = []
    for c in cases:
        dispute = db.query(Dispute).filter(Dispute.id == c.dispute_id).first()
        arb = db.query(Arbitrator).filter(Arbitrator.id == c.arbitrator_id).first() if c.arbitrator_id else None
        results.append({
            "id": c.id, "dispute_id": c.dispute_id,
            "dispute_title": dispute.title if dispute else "N/A",
            "arbitrator_name": arb.name if arb else "Unassigned",
            "status": c.status, "consent_a": c.consent_a, "consent_b": c.consent_b,
            "hearing_datetime": c.hearing_datetime.isoformat() if c.hearing_datetime else None,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })
    return results
