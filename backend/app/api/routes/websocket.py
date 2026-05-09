"""
Madhyastha — WebSocket Routes
Real-time WebSocket for joint mediation sessions + arbitration sessions
"""
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.core.security import verify_party_token
from app.core.websocket_manager import manager
from app.models.models import Dispute, Party, MediationSession, Arbitrator, ArbitrationCase
from app.agents.joint_mediator import JointMediator
from app.rag.retriever import retriever

logger = logging.getLogger("madhyastha.ws")
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/session/{dispute_id}")
async def websocket_session(websocket: WebSocket, dispute_id: str, token: str = Query(...)):
    """WebSocket endpoint for real-time joint mediation (AI mediator)"""
    db = next(get_db_gen())

    try:
        token_data = verify_party_token(token)
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    party = db.query(Party).filter(Party.id == token_data["party_id"]).first()
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not party or not dispute:
        await websocket.close(code=4004, reason="Not found")
        return

    # Check if this dispute is now in arbitration — redirect to arbitration session
    if dispute.status in ["arbitration_hearing"]:
        session = db.query(MediationSession).filter(
            MediationSession.dispute_id == dispute_id, MediationSession.session_type == "arbitration"
        ).first()
    else:
        session = db.query(MediationSession).filter(
            MediationSession.dispute_id == dispute_id, MediationSession.session_type == "ai_mediation"
        ).first()

    await manager.connect(websocket, dispute_id, party.id, party.role)

    try:
        # Send session history
        if session and session.messages:
            await manager.send_personal_message(
                {"type": "history", "messages": session.messages}, websocket
            )

        # Send connection notification
        await manager.broadcast_to_session(dispute_id, {
            "type": "system", "content": f"{party.name} has joined the session.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, exclude_party=party.id)

        # If arbitration session, just relay messages (no AI)
        if dispute.status == "arbitration_hearing":
            while True:
                data = await websocket.receive_json()
                message = data.get("message", "")
                if not message:
                    continue

                user_msg = {
                    "type": "message", "role": party.role, "party_name": party.name,
                    "content": message, "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await manager.send_to_all_in_session(dispute_id, user_msg)

                # Save to DB
                if session:
                    msgs = session.messages or []
                    msgs.append(user_msg)
                    session.messages = msgs
                    db.commit()
        else:
            # AI-mediated session
            synthesis = json.loads(session.ai_brief) if session and session.ai_brief else {}
            precedents = retriever.get_precedents(dispute.title, top_k=3)
            prec_text = "\n".join([f"- {p.get('case_id')}: {p.get('summary', '')}" for p in precedents])

            mediator = JointMediator(
                {"dispute_type": dispute.dispute_type, "title": dispute.title},
                synthesis, prec_text
            )

            while True:
                data = await websocket.receive_json()
                message = data.get("message", "")
                if not message:
                    continue

                # Broadcast user message
                user_msg = {
                    "type": "message", "role": party.role, "party_name": party.name,
                    "content": message, "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await manager.send_to_all_in_session(dispute_id, user_msg)

                # Get AI response
                result = await mediator.mediate(
                    message, party.role, party.name,
                    dispute.round_count + 1, session.messages if session else []
                )

                ai_msg = {
                    "type": "message", "role": "mediator", "party_name": "AI Mediator",
                    "content": result["ai_response"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await manager.send_to_all_in_session(dispute_id, ai_msg)

                # Update DB
                if session:
                    msgs = session.messages or []
                    msgs.append(user_msg)
                    msgs.append(ai_msg)
                    session.messages = msgs
                dispute.round_count += 1

                if result.get("signal") == "AGREEMENT_REACHED":
                    dispute.status = "agreement_pending"
                    if session:
                        session.status = "agreement_reached"
                    await manager.send_to_all_in_session(dispute_id, {
                        "type": "signal", "signal": "AGREEMENT_REACHED",
                        "agreed_option": result.get("agreed_option")
                    })
                elif result.get("signal") == "ESCALATE_TO_ARBITRATION":
                    dispute.status = "escalated_arbitration"
                    dispute.escalation_reason = "AI mediation unable to reach agreement. Escalated to arbitration."
                    if session:
                        session.status = "escalated"
                    await manager.send_to_all_in_session(dispute_id, {
                        "type": "signal", "signal": "ESCALATE_TO_ARBITRATION"
                    })

                db.commit()

    except WebSocketDisconnect:
        manager.disconnect(websocket, dispute_id)
        await manager.broadcast_to_session(dispute_id, {
            "type": "system", "content": f"{party.name} has left the session."
        })
    finally:
        db.close()


@router.websocket("/ws/arbitrator/{dispute_id}")
async def websocket_arbitrator(websocket: WebSocket, dispute_id: str, token: str = Query(...)):
    """WebSocket for arbitrator to join session as human mediator"""
    db = next(get_db_gen())

    # Verify arbitrator token
    try:
        from app.api.routes.arbitrator_auth import verify_arbitrator_token
        payload = verify_arbitrator_token(token)
    except Exception:
        await websocket.close(code=4001, reason="Invalid arbitrator token")
        return

    arb = db.query(Arbitrator).filter(Arbitrator.id == payload["sub"]).first()
    if not arb:
        await websocket.close(code=4004, reason="Arbitrator not found")
        return

    # Find the arbitration session
    session = db.query(MediationSession).filter(
        MediationSession.dispute_id == dispute_id, MediationSession.session_type == "arbitration"
    ).first()
    if not session:
        await websocket.close(code=4004, reason="No arbitration session found")
        return

    await manager.connect(websocket, dispute_id, arb.id, "arbitrator")

    try:
        # Send session history
        if session.messages:
            await manager.send_personal_message(
                {"type": "history", "messages": session.messages}, websocket
            )

        # Announce arbitrator
        await manager.broadcast_to_session(dispute_id, {
            "type": "system",
            "content": f"Arbitrator {arb.name} has joined the session.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, exclude_party=arb.id)

        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            signal = data.get("signal", None)

            if signal == "AGREEMENT_REACHED":
                # Arbitrator declares agreement
                dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
                if dispute:
                    dispute.status = "agreement_pending"
                session.status = "agreement_reached"
                await manager.send_to_all_in_session(dispute_id, {
                    "type": "signal", "signal": "AGREEMENT_REACHED",
                    "agreed_option": data.get("option", "arbitrator_decision")
                })
                db.commit()
                continue

            if not message:
                continue

            # Broadcast arbitrator message
            arb_msg = {
                "type": "message", "role": "arbitrator", "party_name": f"Arb. {arb.name}",
                "content": message, "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await manager.send_to_all_in_session(dispute_id, arb_msg)

            # Save to DB
            msgs = session.messages or []
            msgs.append(arb_msg)
            session.messages = msgs
            db.commit()

    except WebSocketDisconnect:
        manager.disconnect(websocket, dispute_id)
        await manager.broadcast_to_session(dispute_id, {
            "type": "system", "content": f"Arbitrator {arb.name} has left the session."
        })
    finally:
        db.close()


def get_db_gen():
    from app.db.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        pass
