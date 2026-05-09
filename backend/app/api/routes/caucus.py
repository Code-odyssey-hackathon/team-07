"""
Madhyastha — Caucus Routes
Private session: token verification, AI chat, statement submission
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.dependencies import get_db, get_current_party
from app.core.security import verify_party_token
from app.models.models import Dispute, Party, Statement, MediationSession, generate_uuid
from app.schemas.schemas import (
    TokenVerify, TokenVerifyResponse, CaucusChatRequest, CaucusChatResponse,
    StatementSubmit, StatementResponse, MessageResponse
)
from app.agents.caucus_interviewer import CaucusInterviewer
from app.agents.synthesis_analyst import SynthesisAnalyst
from app.rag.retriever import retriever

logger = logging.getLogger("madhyastha.api.caucus")
router = APIRouter(prefix="/caucus", tags=["Caucus — Private Sessions"])

# In-memory chat histories (per party session)
_chat_histories = {}


@router.post("/verify-token", response_model=TokenVerifyResponse)
async def verify_token(data: TokenVerify, db: Session = Depends(get_db)):
    """Validate a party session token"""
    try:
        token_data = verify_party_token(data.token)
        party = db.query(Party).filter(Party.id == token_data["party_id"]).first()
        dispute = db.query(Dispute).filter(Dispute.id == token_data["dispute_id"]).first()
        if not party or not dispute:
            return TokenVerifyResponse(valid=False)
        return TokenVerifyResponse(
            valid=True, party_id=party.id, dispute_id=dispute.id,
            role=party.role, party_name=party.name,
            dispute_title=dispute.title, dispute_type=dispute.dispute_type,
            status=dispute.status
        )
    except Exception:
        return TokenVerifyResponse(valid=False)


@router.post("/chat", response_model=CaucusChatResponse)
async def caucus_chat(
    data: CaucusChatRequest,
    party_info: dict = Depends(get_current_party),
    db: Session = Depends(get_db)
):
    """Send a message to the Caucus Interviewer AI"""
    party = party_info["party"]
    dispute = db.query(Dispute).filter(Dispute.id == party_info["dispute_id"]).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    if party.has_submitted_statement:
        raise HTTPException(status_code=400, detail="Statement already submitted")

    interviewer = CaucusInterviewer({
        "dispute_type": dispute.dispute_type, "title": dispute.title,
        "party_role": party.role, "party_name": party.name,
        "language": party.language
    })

    history_key = f"{dispute.id}_{party.id}"
    if history_key not in _chat_histories:
        _chat_histories[history_key] = []

    result = await interviewer.chat(data.message, _chat_histories[history_key])

    _chat_histories[history_key].append({"role": "user", "content": data.message})
    _chat_histories[history_key].append({"role": "assistant", "content": result["ai_response"]})

    return CaucusChatResponse(
        ai_response=result["ai_response"],
        statement_complete=result["statement_complete"],
        extracted_statement=result.get("extracted_statement")
    )


@router.post("/submit-statement", response_model=StatementResponse)
async def submit_statement(
    data: StatementSubmit,
    party_info: dict = Depends(get_current_party),
    db: Session = Depends(get_db)
):
    """Lock in the party's statement"""
    party = party_info["party"]
    dispute = db.query(Dispute).filter(Dispute.id == party_info["dispute_id"]).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if party.has_submitted_statement:
        raise HTTPException(status_code=400, detail="Statement already submitted")

    history_key = f"{dispute.id}_{party.id}"
    raw_text = json.dumps(_chat_histories.get(history_key, []))

    statement = Statement(
        id=generate_uuid(), dispute_id=dispute.id, party_id=party.id,
        raw_text=raw_text, position=data.position, interest=data.interest,
        min_acceptable=data.min_acceptable, emotional_need=data.emotional_need,
        locked=True, submitted_at=datetime.now(timezone.utc)
    )
    db.add(statement)
    party.has_submitted_statement = True

    # Update dispute status based on which party submitted
    if party.role == "party_a":
        dispute.status = "caucus_a"
    elif party.role == "party_b":
        dispute.status = "caucus_b"

    # Flush so the new statement is visible in subsequent queries
    db.flush()

    # Check if both parties have submitted — trigger synthesis
    other_role = "party_b" if party.role == "party_a" else "party_a"
    other_party = db.query(Party).filter(
        Party.dispute_id == dispute.id, Party.role == other_role
    ).first()

    logger.info(f"Party {party.role} submitted. Other party ({other_role}) submitted: {other_party.has_submitted_statement if other_party else 'NOT FOUND'}")

    if other_party and other_party.has_submitted_statement:
        try:
            await _run_synthesis(dispute, db)
            logger.info(f"Joint session created for dispute {dispute.id}")
        except Exception as e:
            logger.error(f"Synthesis FAILED for dispute {dispute.id}: {e}")
            import traceback
            traceback.print_exc()
            # Still commit the statement even if synthesis fails
            dispute.status = "caucus_b" if party.role == "party_b" else "caucus_a"

    db.commit()
    db.refresh(statement)
    return StatementResponse.model_validate(statement)


async def _run_synthesis(dispute: Dispute, db: Session):
    """Run synthesis when both statements are submitted"""
    logger.info(f"Running synthesis for dispute {dispute.id}...")

    statements = db.query(Statement).filter(Statement.dispute_id == dispute.id).all()
    logger.info(f"Found {len(statements)} statements")

    # Find statements by querying party role directly
    stmt_a = None
    stmt_b = None
    for s in statements:
        party = db.query(Party).filter(Party.id == s.party_id).first()
        if party and party.role == "party_a":
            stmt_a = s
        elif party and party.role == "party_b":
            stmt_b = s

    if not stmt_a or not stmt_b:
        logger.error(f"Missing statements: stmt_a={'found' if stmt_a else 'MISSING'}, stmt_b={'found' if stmt_b else 'MISSING'}")
        return

    logger.info(f"Both statements found. Running AI synthesis...")
    dispute.status = "synthesis"

    precedents = retriever.get_precedents(
        f"{dispute.title} {stmt_a.position} {stmt_b.position}",
        top_k=5, dispute_type=dispute.dispute_type
    )
    logger.info(f"Got {len(precedents)} precedents from RAG")

    analyst = SynthesisAnalyst()
    synthesis = await analyst.analyze(
        {"dispute_type": dispute.dispute_type, "title": dispute.title},
        {"position": stmt_a.position, "interest": stmt_a.interest,
         "min_acceptable": stmt_a.min_acceptable, "emotional_need": stmt_a.emotional_need},
        {"position": stmt_b.position, "interest": stmt_b.interest,
         "min_acceptable": stmt_b.min_acceptable, "emotional_need": stmt_b.emotional_need},
        precedents
    )
    logger.info(f"Synthesis result keys: {list(synthesis.keys()) if synthesis else 'EMPTY'}")

    dispute.common_ground = synthesis.get("overlap_zones", [])
    dispute.settlement_options = synthesis.get("settlement_options", [])
    dispute.status = "joint_session"

    session = MediationSession(
        id=generate_uuid(), dispute_id=dispute.id, session_type="ai_mediation",
        status="active", messages=[{
            "role": "mediator", "content": synthesis.get("recommended_opening", ""),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }], ai_brief=json.dumps(synthesis)
    )
    db.add(session)
    logger.info(f"Synthesis complete. Joint session created for dispute {dispute.id}")
