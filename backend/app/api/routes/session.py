"""
Madhyastha — Session Routes
Joint mediation session REST endpoints
"""
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_party
from app.models.models import Dispute, MediationSession, generate_uuid
from app.schemas.schemas import SessionResponse, SessionMessageRequest, SessionMessageResponse
from app.agents.joint_mediator import JointMediator
from app.rag.retriever import retriever

logger = logging.getLogger("madhyastha.api.session")
router = APIRouter(prefix="/session", tags=["Joint Mediation Session"])


@router.get("/{dispute_id}", response_model=SessionResponse)
async def get_session(dispute_id: str, db: Session = Depends(get_db)):
    """Get session details with AI opening message"""
    session = db.query(MediationSession).filter(
        MediationSession.dispute_id == dispute_id,
        MediationSession.session_type == "ai_mediation"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Caucus phase may not be complete.")
    return SessionResponse.model_validate(session)


@router.post("/{dispute_id}/message", response_model=SessionMessageResponse)
async def send_message(
    dispute_id: str, data: SessionMessageRequest,
    party_info: dict = Depends(get_current_party),
    db: Session = Depends(get_db)
):
    """Send message in joint session (REST fallback for WebSocket)"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if dispute.status != "joint_session":
        raise HTTPException(status_code=400, detail=f"Dispute not in joint session. Status: {dispute.status}")

    session = db.query(MediationSession).filter(
        MediationSession.dispute_id == dispute_id, MediationSession.session_type == "ai_mediation"
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    party = party_info["party"]
    synthesis = json.loads(session.ai_brief) if session.ai_brief else {}
    precedents = retriever.get_precedents(dispute.title, top_k=3, dispute_type=dispute.dispute_type)
    prec_text = "\n".join([f"- {p.get('case_id')}: {p.get('summary', '')}" for p in precedents])

    mediator = JointMediator(
        {"dispute_type": dispute.dispute_type, "title": dispute.title},
        synthesis, prec_text
    )

    result = await mediator.mediate(
        data.message, party.role, party.name,
        dispute.round_count + 1, session.messages or []
    )

    # Update session messages
    msgs = session.messages or []
    msgs.append({"role": party.role, "party_name": party.name,
                 "content": data.message, "timestamp": datetime.now(timezone.utc).isoformat()})
    msgs.append({"role": "mediator", "content": result["ai_response"],
                 "timestamp": datetime.now(timezone.utc).isoformat()})
    session.messages = msgs
    dispute.round_count += 1

    if result.get("signal") == "AGREEMENT_REACHED":
        dispute.status = "agreement_pending"
        session.status = "agreement_reached"
        dispute.final_terms = {"agreed_option": result.get("agreed_option", "B")}
    elif result.get("signal") == "ESCALATE_TO_ARBITRATION":
        dispute.status = "escalated_arbitration"
        session.status = "escalated"
        dispute.escalation_reason = "AI mediation unable to reach agreement. Escalated to arbitration."

    db.commit()
    return SessionMessageResponse(
        ai_response=result["ai_response"], signal=result.get("signal"),
        agreed_option=result.get("agreed_option")
    )
