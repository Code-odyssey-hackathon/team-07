"""
Madhyastha — Pydantic Schemas
Request/Response models for all API endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ─── Dispute Schemas ────────────────────────────────────────────────────────

class PartyInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    phone: Optional[str] = None
    email: Optional[str] = None
    language: str = Field(default="en", max_length=5)


class DisputeRegister(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    description: Optional[str] = None
    dispute_type: str = Field(..., description="Type of civil dispute")
    party_a: PartyInput
    party_b: PartyInput
    arbitration_consent: bool = Field(
        default=False,
        description="Both parties consent to binding arbitration if mediation fails"
    )


class DisputeResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    dispute_type: str
    status: str
    round_count: int
    risk_score: Optional[float] = None
    arbitration_consent: bool
    common_ground: Optional[Dict[str, Any]] = None
    settlement_options: Optional[List[Dict[str, Any]]] = None
    final_terms: Optional[Dict[str, Any]] = None
    escalation_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DisputeRegistrationResult(BaseModel):
    dispute: DisputeResponse
    party_a_token: str
    party_b_token: str
    party_a_link: str
    party_b_link: str
    message: str


class DisputeStatusResponse(BaseModel):
    id: str
    title: str
    status: str
    dispute_type: str
    round_count: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Party Schemas ──────────────────────────────────────────────────────────

class PartyResponse(BaseModel):
    id: str
    dispute_id: str
    role: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    language: str
    has_submitted_statement: bool
    has_signed_agreement: bool
    arbitration_consent: bool

    class Config:
        from_attributes = True


# ─── Caucus Schemas ─────────────────────────────────────────────────────────

class TokenVerify(BaseModel):
    token: str


class TokenVerifyResponse(BaseModel):
    valid: bool
    party_id: Optional[str] = None
    dispute_id: Optional[str] = None
    role: Optional[str] = None
    party_name: Optional[str] = None
    dispute_title: Optional[str] = None
    dispute_type: Optional[str] = None
    language: Optional[str] = None
    status: Optional[str] = None


class CaucusChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class CaucusChatResponse(BaseModel):
    ai_response: str
    statement_complete: bool = False
    extracted_statement: Optional[Dict[str, str]] = None


class StatementSubmit(BaseModel):
    position: str
    interest: str
    min_acceptable: str
    emotional_need: Optional[str] = None


class StatementResponse(BaseModel):
    id: str
    dispute_id: str
    party_id: str
    position: Optional[str] = None
    interest: Optional[str] = None
    min_acceptable: Optional[str] = None
    emotional_need: Optional[str] = None
    locked: bool
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Session Schemas ────────────────────────────────────────────────────────

class SessionResponse(BaseModel):
    id: str
    dispute_id: str
    session_type: str
    status: str
    messages: Optional[List[Dict[str, Any]]] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)


class SessionMessageResponse(BaseModel):
    ai_response: str
    signal: Optional[str] = None  # AGREEMENT_REACHED | ESCALATE_TO_HUMAN
    agreed_option: Optional[str] = None


# ─── Agreement Schemas ──────────────────────────────────────────────────────

class AgreementResponse(BaseModel):
    id: str
    dispute_id: str
    agreement_type: str
    terms: Optional[Dict[str, Any]] = None
    party_a_signed: bool
    party_b_signed: bool
    arbitrator_signed: bool = False
    party_a_signed_at: Optional[datetime] = None
    party_b_signed_at: Optional[datetime] = None
    arbitrator_signed_at: Optional[datetime] = None
    arbitrator_name: Optional[str] = None
    finalized_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SignatureRequest(BaseModel):
    signature_data: str = Field(..., description="Base64 encoded signature image")


# ─── Arbitration Schemas ────────────────────────────────────────────────────

class ArbitrationCaseResponse(BaseModel):
    id: str
    dispute_id: str
    arbitrator_id: Optional[str] = None
    arbitrator_name: Optional[str] = None
    status: str
    consent_a: bool
    consent_b: bool
    hearing_datetime: Optional[datetime] = None
    hearing_link: Optional[str] = None
    award: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ArbitrationConsentRequest(BaseModel):
    consent: bool = True


class HearingScheduleRequest(BaseModel):
    hearing_datetime: datetime
    hearing_link: str = Field(..., description="Video call link for the hearing")


class AwardSubmitRequest(BaseModel):
    award_type: str = Field(
        ..., description="full_payment | partial_payment | asset_transfer | dismissal"
    )
    amount: Optional[float] = None
    currency: str = "INR"
    payment_timeline_days: Optional[int] = None
    installments: Optional[int] = None
    enforcement_clause: Optional[str] = None
    reasoning: str = Field(..., description="Legal reasoning for the award")


# ─── Court Filing Schemas ───────────────────────────────────────────────────

class CourtFilingResponse(BaseModel):
    dispute_id: str
    petition_available: bool
    evidence_bundle_available: bool
    ecourts_link: str
    message: str


# ─── Stats / Admin Schemas ──────────────────────────────────────────────────

class StatsSummary(BaseModel):
    total_disputes: int
    active_disputes: int
    resolved_disputes: int
    escalated_to_arbitration: int
    court_filings: int
    resolution_rate: float
    disputes_by_type: Dict[str, int]
    disputes_by_status: Dict[str, int]


# ─── Generic ────────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    success: bool = True


# ─── Civic Event Schemas ────────────────────────────────────────────────────

class CivicEventCreate(BaseModel):
    event_type: str = Field(..., description="rera_complaint | land_mutation_rejection | cpgrams_escalation | cersai_flag")
    party_identifier: str = Field(..., description="Property ID or party identifier")
    source: str = Field(..., description="rera | cpgrams | land_registry | cersai")
    event_date: datetime
    district: Optional[str] = None
    state: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CivicEventResponse(BaseModel):
    id: str
    event_type: str
    party_identifier: str
    source: str
    event_date: datetime
    district: Optional[str] = None
    state: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Risk Score Schemas ─────────────────────────────────────────────────────

class RiskScoreRequest(BaseModel):
    party_identifier: str = Field(..., description="Party or property ID to score")
    events: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional explicit events. If not provided, fetched from DB."
    )


class RiskScoreResponse(BaseModel):
    party_identifier: str
    risk_score: float = Field(..., ge=0, le=100)
    dispute_probability: float
    predicted_dispute_type: str
    nudge_recommended: bool
    feature_breakdown: Dict[str, Any]
    model_info: Optional[Dict[str, Any]] = None


class NudgeResponse(BaseModel):
    party_identifier: str
    nudge_sent: bool
    message: str
    language: str
    channel: str = "whatsapp_mock"

