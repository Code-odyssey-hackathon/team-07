"""
Madhyastha — SQLAlchemy Models
All 7 database models for the dispute resolution platform
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float,
    DateTime, JSON, ForeignKey
)
from sqlalchemy.orm import relationship
from app.db.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ── Dispute Types ───────────────────────────────────────────────────────────
DISPUTE_TYPES = [
    "property_boundary", "property_ownership", "rent_tenancy",
    "money_loan", "contract_breach", "employment", "consumer",
    "family_inheritance", "neighbourhood", "other_civil"
]

# ── Dispute Statuses ────────────────────────────────────────────────────────
DISPUTE_STATUSES = [
    "registered", "awaiting_party_b", "caucus_a", "caucus_b",
    "synthesis", "joint_session", "agreement_pending", "resolved",
    "escalated_human", "escalated_arbitration", "arbitration_hearing",
    "award_issued", "court_filing", "closed"
]

# ── Supported Languages ────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = {
    "hi": "Hindi", "kn": "Kannada", "ta": "Tamil",
    "te": "Telugu", "mr": "Marathi", "bn": "Bengali",
    "gu": "Gujarati", "pa": "Punjabi", "ml": "Malayalam",
    "en": "English"
}


class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    dispute_type = Column(String(50), nullable=False)
    status = Column(String(50), default="registered", nullable=False)
    common_ground = Column(JSON, nullable=True)
    settlement_options = Column(JSON, nullable=True)
    final_terms = Column(JSON, nullable=True)
    escalation_reason = Column(Text, nullable=True)
    round_count = Column(Integer, default=0)
    arbitration_consent = Column(Boolean, default=False)
    risk_score = Column(Float, nullable=True)  # 0-100 from ML risk scorer
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    parties = relationship("Party", back_populates="dispute", cascade="all, delete-orphan")
    statements = relationship("Statement", back_populates="dispute", cascade="all, delete-orphan")
    sessions = relationship("MediationSession", back_populates="dispute", cascade="all, delete-orphan")
    agreements = relationship("Agreement", back_populates="dispute", cascade="all, delete-orphan")
    arbitration_cases = relationship("ArbitrationCase", back_populates="dispute", cascade="all, delete-orphan")


class Party(Base):
    __tablename__ = "parties"

    id = Column(String, primary_key=True, default=generate_uuid)
    dispute_id = Column(String, ForeignKey("disputes.id"), nullable=False)
    role = Column(String(20), nullable=False)  # party_a | party_b
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    language = Column(String(5), default="en")
    session_token = Column(String(500), nullable=True)
    has_submitted_statement = Column(Boolean, default=False)
    has_signed_agreement = Column(Boolean, default=False)
    arbitration_consent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    dispute = relationship("Dispute", back_populates="parties")
    statements = relationship("Statement", back_populates="party", cascade="all, delete-orphan")


class Statement(Base):
    __tablename__ = "statements"

    id = Column(String, primary_key=True, default=generate_uuid)
    dispute_id = Column(String, ForeignKey("disputes.id"), nullable=False)
    party_id = Column(String, ForeignKey("parties.id"), nullable=False)
    raw_text = Column(Text, nullable=True)
    position = Column(Text, nullable=True)
    interest = Column(Text, nullable=True)
    min_acceptable = Column(Text, nullable=True)
    emotional_need = Column(Text, nullable=True)
    locked = Column(Boolean, default=False)
    submitted_at = Column(DateTime, nullable=True)

    # Relationships
    dispute = relationship("Dispute", back_populates="statements")
    party = relationship("Party", back_populates="statements")


class MediationSession(Base):
    __tablename__ = "mediation_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    dispute_id = Column(String, ForeignKey("disputes.id"), nullable=False)
    session_type = Column(String(30), nullable=False)  # ai_mediation | arbitration
    status = Column(String(30), default="active")  # active | agreement_reached | escalated | failed
    messages = Column(JSON, default=list)
    ai_brief = Column(Text, nullable=True)
    started_at = Column(DateTime, default=utc_now)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    dispute = relationship("Dispute", back_populates="sessions")


class Agreement(Base):
    __tablename__ = "agreements"

    id = Column(String, primary_key=True, default=generate_uuid)
    dispute_id = Column(String, ForeignKey("disputes.id"), nullable=False)
    agreement_type = Column(String(30), nullable=False)  # mediation_settlement | arbitration_award
    terms = Column(JSON, nullable=True)
    pdf_path = Column(String(500), nullable=True)
    party_a_signed = Column(Boolean, default=False)
    party_b_signed = Column(Boolean, default=False)
    arbitrator_signed = Column(Boolean, default=False)  # Arbitrator digital signature
    party_a_signed_at = Column(DateTime, nullable=True)
    party_b_signed_at = Column(DateTime, nullable=True)
    arbitrator_signed_at = Column(DateTime, nullable=True)
    arbitrator_name = Column(String(200), nullable=True)  # Name of signing arbitrator
    finalized_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    dispute = relationship("Dispute", back_populates="agreements")


class ArbitrationCase(Base):
    __tablename__ = "arbitration_cases"

    id = Column(String, primary_key=True, default=generate_uuid)
    dispute_id = Column(String, ForeignKey("disputes.id"), nullable=False)
    arbitrator_id = Column(String, ForeignKey("arbitrators.id"), nullable=True)
    status = Column(String(30), default="pending_consent")
    # pending_consent | assigned | hearing_scheduled | award_issued | declined
    consent_a = Column(Boolean, default=False)
    consent_b = Column(Boolean, default=False)
    ai_brief = Column(Text, nullable=True)
    ai_brief_pdf_path = Column(String(500), nullable=True)
    hearing_datetime = Column(DateTime, nullable=True)
    hearing_link = Column(String(500), nullable=True)
    award = Column(JSON, nullable=True)
    award_pdf_path = Column(String(500), nullable=True)
    issued_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    dispute = relationship("Dispute", back_populates="arbitration_cases")
    arbitrator = relationship("Arbitrator", back_populates="cases")


class Arbitrator(Base):
    __tablename__ = "arbitrators"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(500), nullable=True)  # For dashboard login
    bar_registration = Column(String(100), nullable=True)
    specializations = Column(JSON, default=list)
    languages = Column(JSON, default=list)
    available = Column(Boolean, default=True)
    cases_assigned = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    cases = relationship("ArbitrationCase", back_populates="arbitrator")


class CivicEvent(Base):
    """Civic data events from RERA, CPGrams, Land Registry, CERSAI"""
    __tablename__ = "civic_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    event_type = Column(String(100), nullable=False)
    # rera_complaint | land_mutation_rejection | cpgrams_escalation | cersai_flag
    party_identifier = Column(String(200), nullable=False)  # property ID or party ID
    source = Column(String(50), nullable=False)  # rera | cpgrams | land_registry | cersai
    event_date = Column(DateTime, nullable=False)
    district = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    event_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)


class RiskScore(Base):
    """ML-computed risk scores for parties/properties"""
    __tablename__ = "risk_scores"

    id = Column(String, primary_key=True, default=generate_uuid)
    party_identifier = Column(String(200), nullable=False)
    score = Column(Float, nullable=False)  # 0-100
    dispute_type_predicted = Column(String(50), nullable=True)
    nudge_sent = Column(Boolean, default=False)
    nudge_language = Column(String(5), default="en")
    nudge_message = Column(Text, nullable=True)  # stored mock WhatsApp message
    computed_at = Column(DateTime, default=utc_now)
