"""
Madhyastha — Arbitrator Auth Routes
Login and registration for certified arbitrators
"""
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from jose import jwt, JWTError
from app.core.config import settings
from app.core.dependencies import get_db
from app.models.models import Arbitrator, ArbitrationCase, Dispute, MediationSession, Party, Statement, generate_uuid

logger = logging.getLogger("madhyastha.api.arbitrator_auth")
router = APIRouter(prefix="/arbitrator", tags=["Arbitrator Dashboard"])


# ─── Schemas ────────────────────────────────────────────────────────────────

class ArbitratorRegister(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    password: str
    bar_registration: Optional[str] = None
    specializations: Optional[List[str]] = []
    languages: Optional[List[str]] = ["en"]

class ArbitratorLogin(BaseModel):
    email: str
    password: str

class ArbitratorToken(BaseModel):
    token: str
    arbitrator_id: str
    name: str
    email: str

class CaseDetail(BaseModel):
    case_id: str
    dispute_id: str
    dispute_title: str
    dispute_type: str
    status: str
    party_a_name: Optional[str] = None
    party_b_name: Optional[str] = None
    escalation_reason: Optional[str] = None
    created_at: Optional[str] = None
    ai_brief: Optional[str] = None

class ArbitratorDashboard(BaseModel):
    arbitrator: dict
    pending_cases: List[CaseDetail]
    active_cases: List[CaseDetail]
    completed_cases: List[CaseDetail]


# ─── Helpers ────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_arbitrator_token(arbitrator_id: str) -> str:
    payload = {
        "sub": arbitrator_id,
        "type": "arbitrator",
        "exp": datetime.now(timezone.utc) + timedelta(hours=72),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def verify_arbitrator_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "arbitrator":
            raise ValueError("Not an arbitrator token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token type")


# ─── Routes ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=ArbitratorToken)
async def register_arbitrator(data: ArbitratorRegister, db: Session = Depends(get_db)):
    """Register a new arbitrator"""
    existing = db.query(Arbitrator).filter(Arbitrator.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    arb = Arbitrator(
        id=generate_uuid(), name=data.name, email=data.email, phone=data.phone,
        password_hash=hash_password(data.password),
        bar_registration=data.bar_registration,
        specializations=data.specializations, languages=data.languages,
    )
    db.add(arb)
    db.commit()

    token = create_arbitrator_token(arb.id)
    logger.info(f"Arbitrator registered: {arb.name} ({arb.email})")
    return ArbitratorToken(token=token, arbitrator_id=arb.id, name=arb.name, email=arb.email)


@router.post("/login", response_model=ArbitratorToken)
async def login_arbitrator(data: ArbitratorLogin, db: Session = Depends(get_db)):
    """Arbitrator login"""
    arb = db.query(Arbitrator).filter(Arbitrator.email == data.email).first()
    if not arb or arb.password_hash != hash_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_arbitrator_token(arb.id)
    logger.info(f"Arbitrator logged in: {arb.name}")
    return ArbitratorToken(token=token, arbitrator_id=arb.id, name=arb.name, email=arb.email)


@router.get("/dashboard", response_model=ArbitratorDashboard)
async def get_dashboard(token: str, db: Session = Depends(get_db)):
    """Get arbitrator dashboard with all assigned cases"""
    payload = verify_arbitrator_token(token)
    arb = db.query(Arbitrator).filter(Arbitrator.id == payload["sub"]).first()
    if not arb:
        raise HTTPException(status_code=404, detail="Arbitrator not found")

    cases = db.query(ArbitrationCase).filter(ArbitrationCase.arbitrator_id == arb.id).all()

    def build_case_detail(ac):
        dispute = db.query(Dispute).filter(Dispute.id == ac.dispute_id).first()
        parties = db.query(Party).filter(Party.dispute_id == ac.dispute_id).all()
        pa = next((p for p in parties if p.role == "party_a"), None)
        pb = next((p for p in parties if p.role == "party_b"), None)
        return CaseDetail(
            case_id=ac.id, dispute_id=ac.dispute_id,
            dispute_title=dispute.title if dispute else "Unknown",
            dispute_type=dispute.dispute_type if dispute else "unknown",
            status=ac.status,
            party_a_name=pa.name if pa else None,
            party_b_name=pb.name if pb else None,
            escalation_reason=dispute.escalation_reason if dispute else None,
            created_at=ac.created_at.isoformat() if ac.created_at else None,
            ai_brief=ac.ai_brief,
        )

    pending = [build_case_detail(c) for c in cases if c.status in ["pending_consent", "assigned"]]
    active = [build_case_detail(c) for c in cases if c.status in ["accepted", "hearing_scheduled"]]
    completed = [build_case_detail(c) for c in cases if c.status in ["award_issued", "declined"]]

    return ArbitratorDashboard(
        arbitrator={"id": arb.id, "name": arb.name, "email": arb.email,
                    "bar_registration": arb.bar_registration, "cases_assigned": arb.cases_assigned},
        pending_cases=pending, active_cases=active, completed_cases=completed,
    )


@router.get("/available")
async def list_available_arbitrators(db: Session = Depends(get_db)):
    """List all available arbitrators for party selection"""
    arbs = db.query(Arbitrator).filter(Arbitrator.available == True).all()
    return [
        {"id": a.id, "name": a.name, "bar_registration": a.bar_registration,
         "specializations": a.specializations, "languages": a.languages,
         "cases_assigned": a.cases_assigned}
        for a in arbs
    ]


@router.post("/{dispute_id}/assign")
async def assign_arbitrator(dispute_id: str, arbitrator_id: str, db: Session = Depends(get_db)):
    """Party selects and assigns an arbitrator — AI generates a case report"""
    from app.services.groq_service import groq_service
    import json

    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    arb = db.query(Arbitrator).filter(Arbitrator.id == arbitrator_id).first()
    if not arb:
        raise HTTPException(status_code=404, detail="Arbitrator not found")

    # Check if case already exists
    existing = db.query(ArbitrationCase).filter(ArbitrationCase.dispute_id == dispute_id).first()
    if existing:
        return {"message": "Case already assigned", "case_id": existing.id}

    # ── Collect all case data ────────────────────────────────────────────
    session = db.query(MediationSession).filter(
        MediationSession.dispute_id == dispute_id).order_by(MediationSession.started_at.desc()).first()
    stmts = db.query(Statement).filter(Statement.dispute_id == dispute_id).all()
    parties = db.query(Party).filter(Party.dispute_id == dispute_id).all()
    pa = next((p for p in parties if p.role == "party_a"), None)
    pb = next((p for p in parties if p.role == "party_b"), None)
    stmt_a = next((s for s in stmts if pa and s.party_id == pa.id), None)
    stmt_b = next((s for s in stmts if pb and s.party_id == pb.id), None)

    # Build chat transcript
    transcript = ""
    if session and session.messages:
        for msg in session.messages[-30:]:  # Last 30 messages
            role = msg.get("party_name", msg.get("role", "unknown"))
            transcript += f"[{role}]: {msg.get('content', '')}\n"

    # ── Generate AI Report ───────────────────────────────────────────────
    report_prompt = f"""You are a legal analyst preparing a comprehensive case report for an arbitrator 
under the Arbitration & Conciliation Act, 1996 (India).

Generate a structured case report in JSON format with these exact fields:

DISPUTE DETAILS:
- Title: {dispute.title}
- Type: {dispute.dispute_type}
- Rounds of mediation: {dispute.round_count}
- Escalation reason: {dispute.escalation_reason or 'AI mediation could not reach agreement'}

PARTY A ({pa.name if pa else 'Unknown'}):
- Position: {stmt_a.position if stmt_a else 'Not recorded'}
- Interest: {stmt_a.interest if stmt_a else 'Not recorded'}
- Minimum acceptable: {stmt_a.min_acceptable if stmt_a else 'Not recorded'}
- Emotional need: {stmt_a.emotional_need if stmt_a else 'Not recorded'}

PARTY B ({pb.name if pb else 'Unknown'}):
- Position: {stmt_b.position if stmt_b else 'Not recorded'}
- Interest: {stmt_b.interest if stmt_b else 'Not recorded'}
- Minimum acceptable: {stmt_b.min_acceptable if stmt_b else 'Not recorded'}
- Emotional need: {stmt_b.emotional_need if stmt_b else 'Not recorded'}

MEDIATION TRANSCRIPT (last messages):
{transcript or 'No transcript available'}

COMMON GROUND IDENTIFIED: {json.dumps(dispute.common_ground) if dispute.common_ground else 'None identified'}

Return a JSON object with these keys:
{{
    "case_summary": "2-3 paragraph overview of the dispute",
    "party_a_analysis": "Analysis of Party A's position, strengths, weaknesses",
    "party_b_analysis": "Analysis of Party B's position, strengths, weaknesses",
    "mediation_history": "Summary of what happened during AI mediation and why it failed",
    "key_issues": ["list of 3-5 key legal/factual issues to resolve"],
    "common_ground": ["areas where parties showed potential agreement"],
    "applicable_law": ["relevant sections of Indian law applicable"],
    "recommended_approach": "Recommended arbitration strategy for fair resolution",
    "risk_assessment": "Assessment of risks if this goes to court instead"
}}"""

    try:
        report = await groq_service.chat_json(
            system_prompt=report_prompt,
            user_message="Generate the arbitration case report now.",
            temperature=0.3, max_tokens=4096
        )
        logger.info(f"AI case report generated for dispute {dispute_id}")
    except Exception as e:
        logger.error(f"AI report generation failed: {e}")
        report = {
            "case_summary": f"Dispute '{dispute.title}' ({dispute.dispute_type}) escalated after {dispute.round_count} rounds of AI mediation failed to reach agreement.",
            "party_a_analysis": f"{pa.name if pa else 'Party A'}: {stmt_a.position if stmt_a else 'Position not recorded'}",
            "party_b_analysis": f"{pb.name if pb else 'Party B'}: {stmt_b.position if stmt_b else 'Position not recorded'}",
            "mediation_history": dispute.escalation_reason or "AI mediation unable to reach agreement.",
            "key_issues": ["Core dispute on terms", "Timeline disagreement"],
            "common_ground": dispute.common_ground or [],
            "applicable_law": ["Arbitration & Conciliation Act, 1996"],
            "recommended_approach": "Review both positions and propose a balanced settlement.",
            "risk_assessment": "Court proceedings would be costly and time-consuming for both parties."
        }

    ai_brief_json = json.dumps(report)

    arb_case = ArbitrationCase(
        id=generate_uuid(), dispute_id=dispute_id, arbitrator_id=arb.id,
        status="assigned", ai_brief=ai_brief_json,
    )
    db.add(arb_case)
    arb.cases_assigned += 1
    dispute.status = "escalated_arbitration"
    db.commit()

    logger.info(f"Arbitrator {arb.name} assigned to dispute {dispute_id}")
    return {"message": f"Arbitrator {arb.name} assigned successfully", "case_id": arb_case.id}


@router.post("/{dispute_id}/accept")
async def accept_case(dispute_id: str, token: str, db: Session = Depends(get_db)):
    """Arbitrator accepts a case and joins the session"""
    payload = verify_arbitrator_token(token)
    arb = db.query(Arbitrator).filter(Arbitrator.id == payload["sub"]).first()
    if not arb:
        raise HTTPException(status_code=404, detail="Arbitrator not found")

    arb_case = db.query(ArbitrationCase).filter(
        ArbitrationCase.dispute_id == dispute_id, ArbitrationCase.arbitrator_id == arb.id
    ).first()
    if not arb_case:
        raise HTTPException(status_code=404, detail="Case not found")

    arb_case.status = "accepted"

    # Create or reuse arbitration session
    session = db.query(MediationSession).filter(
        MediationSession.dispute_id == dispute_id, MediationSession.session_type == "arbitration"
    ).first()
    if not session:
        session = MediationSession(
            id=generate_uuid(), dispute_id=dispute_id, session_type="arbitration",
            status="active", messages=[{
                "role": "system",
                "content": f"Arbitrator {arb.name} has accepted the case and joined the session.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }], ai_brief=arb_case.ai_brief
        )
        db.add(session)

    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if dispute:
        dispute.status = "arbitration_hearing"

    db.commit()
    logger.info(f"Arbitrator {arb.name} accepted case for dispute {dispute_id}")
    return {"message": "Case accepted. You can now join the session.", "session_id": session.id}
