"""
NyayaAI — Risk & Prevention Engine API Routes
Endpoints for civic event ingestion, risk scoring, and WhatsApp nudge (mock).
"""

import logging
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.models import CivicEvent, RiskScore, generate_uuid
from app.schemas.schemas import (
    CivicEventCreate, CivicEventResponse,
    RiskScoreRequest, RiskScoreResponse,
    NudgeResponse, MessageResponse
)
from app.core.config import settings

logger = logging.getLogger("madhyastha.risk")

router = APIRouter(tags=["Prevention Engine"])


# ── Civic Event Ingestion ───────────────────────────────────────────────────

@router.post("/civic/ingest", response_model=CivicEventResponse,
             summary="Ingest a civic event from RERA/CPGrams/Land Registry/CERSAI")
async def ingest_civic_event(event: CivicEventCreate, db: Session = Depends(get_db)):
    """Ingest a civic data event into the prevention engine."""
    db_event = CivicEvent(
        id=generate_uuid(),
        event_type=event.event_type,
        party_identifier=event.party_identifier,
        source=event.source,
        event_date=event.event_date,
        district=event.district,
        state=event.state,
        event_metadata=event.metadata or {},
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    logger.info(f"Civic event ingested: {event.event_type} from {event.source} for {event.party_identifier}")
    return db_event


@router.get("/civic/events/{party_identifier}", response_model=List[CivicEventResponse],
            summary="Get civic event trail for a party/property")
async def get_civic_events(party_identifier: str, db: Session = Depends(get_db)):
    """Retrieve all civic events for a given party or property identifier."""
    events = (
        db.query(CivicEvent)
        .filter(CivicEvent.party_identifier == party_identifier)
        .order_by(CivicEvent.event_date.desc())
        .all()
    )
    return events


# ── Risk Scoring ────────────────────────────────────────────────────────────

@router.post("/risk/score", response_model=RiskScoreResponse,
             summary="Compute risk score using LightGBM model")
async def compute_risk_score(request: RiskScoreRequest, db: Session = Depends(get_db)):
    """
    Compute dispute risk score for a party/property using the trained LightGBM model.
    If events are not provided in the request, they are fetched from the DB.
    """
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    # Get events — from request or DB
    if request.events:
        events = request.events
    else:
        db_events = (
            db.query(CivicEvent)
            .filter(CivicEvent.party_identifier == request.party_identifier)
            .order_by(CivicEvent.event_date.asc())
            .all()
        )
        if not db_events:
            raise HTTPException(status_code=404, detail=f"No civic events found for {request.party_identifier}")

        events = [
            {
                "event_type": e.event_type,
                "source": e.source,
                "event_date": e.event_date.isoformat() if e.event_date else None,
            }
            for e in db_events
        ]

    # Run prediction
    try:
        from ml.risk_scorer.predict import predict_risk, get_model_info
        prediction = predict_risk(events, nudge_threshold=settings.NUDGE_THRESHOLD)
        model_info = get_model_info()
    except Exception as e:
        logger.error(f"Risk prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Risk prediction failed: {str(e)}")

    # Store result
    risk_record = RiskScore(
        id=generate_uuid(),
        party_identifier=request.party_identifier,
        score=prediction.risk_score,
        dispute_type_predicted=prediction.predicted_dispute_type,
        computed_at=datetime.now(timezone.utc),
    )
    db.add(risk_record)
    db.commit()

    logger.info(f"Risk score computed: {request.party_identifier} → {prediction.risk_score}")

    return RiskScoreResponse(
        party_identifier=request.party_identifier,
        risk_score=prediction.risk_score,
        dispute_probability=prediction.dispute_probability,
        predicted_dispute_type=prediction.predicted_dispute_type,
        nudge_recommended=prediction.nudge_recommended,
        feature_breakdown=prediction.feature_breakdown,
        model_info=model_info,
    )


# ── WhatsApp Nudge (Mock) ──────────────────────────────────────────────────

NUDGE_TEMPLATES = {
    "en": "⚠️ NyayaAI Alert: We've detected potential dispute signals related to your property/case ({party_id}). Risk Score: {score}/100. Resolve early with free AI mediation at madhyastha.in. Don't let it reach court!",
    "hi": "⚠️ न्यायAI चेतावनी: आपकी संपत्ति/मामले ({party_id}) से संबंधित विवाद संकेत मिले हैं। जोखिम स्कोर: {score}/100। madhyastha.in पर मुफ्त AI मध्यस्थता से जल्दी हल करें!",
    "kn": "⚠️ ನ್ಯಾಯAI ಎಚ್ಚರಿಕೆ: ನಿಮ್ಮ ಆಸ್ತಿ/ಪ್ರಕರಣಕ್ಕೆ ({party_id}) ಸಂಬಂಧಿಸಿದ ವಿವಾದ ಸಂಕೇತಗಳು ಪತ್ತೆಯಾಗಿವೆ। ಅಪಾಯ ಸ್ಕೋರ್: {score}/100. madhyastha.in ನಲ್ಲಿ ಉಚಿತ AI ಮಧ್ಯಸ್ಥಿಕೆಯ ಮೂಲಕ ಬೇಗ ಪರಿಹರಿಸಿ!",
    "ta": "⚠️ நியாயAI எச்சரிக்கை: உங்கள் சொத்து/வழக்கு ({party_id}) தொடர்பான தகராறு சிக்னல்கள் கண்டறியப்பட்டன। ஆபத்து மதிப்பெண்: {score}/100. madhyastha.in இல் இலவச AI மத்தியஸ்தம் மூலம் விரைவாக தீர்க்கவும்!",
}


@router.post("/risk/nudge/{party_identifier}", response_model=NudgeResponse,
             summary="Send WhatsApp nudge for high-risk score (mock)")
async def send_nudge(party_identifier: str, language: str = "en", db: Session = Depends(get_db)):
    """
    Mock WhatsApp nudge endpoint. Generates and stores the message
    instead of actually sending it via Gupshup/Meta Cloud API.
    """
    # Get latest risk score
    latest_score = (
        db.query(RiskScore)
        .filter(RiskScore.party_identifier == party_identifier)
        .order_by(RiskScore.computed_at.desc())
        .first()
    )

    if not latest_score:
        raise HTTPException(status_code=404, detail=f"No risk score found for {party_identifier}. Run /risk/score first.")

    if latest_score.score < settings.NUDGE_THRESHOLD:
        return NudgeResponse(
            party_identifier=party_identifier,
            nudge_sent=False,
            message=f"Score {latest_score.score} is below threshold {settings.NUDGE_THRESHOLD}. No nudge needed.",
            language=language,
            channel="whatsapp_mock",
        )

    # Generate message
    template = NUDGE_TEMPLATES.get(language, NUDGE_TEMPLATES["en"])
    message = template.format(party_id=party_identifier, score=latest_score.score)

    # Store the mock nudge (instead of sending via WhatsApp API)
    latest_score.nudge_sent = True
    latest_score.nudge_language = language
    latest_score.nudge_message = message
    db.commit()

    logger.info(f"[MOCK WHATSAPP] Nudge sent to {party_identifier} in {language}: score={latest_score.score}")

    return NudgeResponse(
        party_identifier=party_identifier,
        nudge_sent=True,
        message=message,
        language=language,
        channel="whatsapp_mock",
    )


# ── Risk Score History ──────────────────────────────────────────────────────

@router.get("/risk/history/{party_identifier}",
            summary="Get risk score history for a party")
async def get_risk_history(party_identifier: str, db: Session = Depends(get_db)):
    """Get all computed risk scores for a party/property."""
    scores = (
        db.query(RiskScore)
        .filter(RiskScore.party_identifier == party_identifier)
        .order_by(RiskScore.computed_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": s.id,
            "score": s.score,
            "dispute_type_predicted": s.dispute_type_predicted,
            "nudge_sent": s.nudge_sent,
            "nudge_language": s.nudge_language,
            "nudge_message": s.nudge_message,
            "computed_at": s.computed_at.isoformat() if s.computed_at else None,
        }
        for s in scores
    ]


# ── Model Info ──────────────────────────────────────────────────────────────

@router.get("/risk/model-info", summary="Get risk scorer model information")
async def model_info():
    """Returns info about the loaded LightGBM model."""
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        from ml.risk_scorer.predict import get_model_info
        return get_model_info()
    except Exception as e:
        return {"status": "error", "detail": str(e)}
