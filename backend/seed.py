"""
Madhyastha — Database Seeder
Creates sample disputes at various stages for demo + civic events for prevention engine
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.database import init_db, SessionLocal
from app.models.models import (
    Dispute, Party, Statement, MediationSession, Arbitrator,
    CivicEvent, RiskScore, generate_uuid
)
from app.core.security import create_party_token
from datetime import datetime, timezone, timedelta
import json


def seed():
    init_db()
    db = SessionLocal()

    # Clear existing data
    db.query(RiskScore).delete()
    db.query(CivicEvent).delete()
    db.query(Statement).delete()
    db.query(MediationSession).delete()
    db.query(Party).delete()
    db.query(Dispute).delete()
    db.commit()

    print("[SEED] Seeding Madhyastha database...\n")

    # ── Dispute 1: Active — Awaiting Party B ────────────────────────
    d1_id = generate_uuid()
    d1 = Dispute(id=d1_id, title="Loan Repayment Dispute — Rs 5 Lakhs",
                 description="Business partner loan dispute",
                 dispute_type="money_loan", status="awaiting_party_b",
                 arbitration_consent=True, risk_score=45.2)
    db.add(d1)
    p1a = Party(id=generate_uuid(), dispute_id=d1_id, role="party_a",
                name="Rajesh Kumar", phone="9876543210", email="rajesh@example.com",
                language="en", arbitration_consent=True)
    p1a.session_token = create_party_token(p1a.id, d1_id, "party_a")
    p1b = Party(id=generate_uuid(), dispute_id=d1_id, role="party_b",
                name="Suresh Patel", phone="9876543211", email="suresh@example.com",
                language="en", arbitration_consent=True)
    p1b.session_token = create_party_token(p1b.id, d1_id, "party_b")
    db.add_all([p1a, p1b])
    print(f"  [OK] Dispute 1: {d1.title}")
    print(f"    Party A token: {p1a.session_token[:40]}...")
    print(f"    Party B token: {p1b.session_token[:40]}...")

    # ── Dispute 2: Joint Session Ready ──────────────────────────────
    d2_id = generate_uuid()
    d2 = Dispute(id=d2_id, title="Property Boundary Dispute — Shared Wall",
                 dispute_type="property_boundary", status="joint_session",
                 arbitration_consent=True, round_count=0, risk_score=72.8,
                 settlement_options=[
                     {"option_id": "A", "title": "Shared Wall Maintenance",
                      "terms": "Both share 50-50 maintenance cost", "timeline": "Immediate",
                      "favors": "neutral", "precedent_ref": "IK/2023/12890"},
                     {"option_id": "B", "title": "Wall Reconstruction",
                      "terms": "Rebuild wall at boundary with cost split 60-40",
                      "timeline": "90 days", "favors": "party_a", "precedent_ref": "IK/2023/44567"}
                 ])
    db.add(d2)
    p2a = Party(id=generate_uuid(), dispute_id=d2_id, role="party_a",
                name="Anita Sharma", phone="9876543220", email="anita@example.com",
                language="hi", has_submitted_statement=True, arbitration_consent=True)
    p2a.session_token = create_party_token(p2a.id, d2_id, "party_a")
    p2b = Party(id=generate_uuid(), dispute_id=d2_id, role="party_b",
                name="Mohan Singh", phone="9876543221", email="mohan@example.com",
                language="hi", has_submitted_statement=True, arbitration_consent=True)
    p2b.session_token = create_party_token(p2b.id, d2_id, "party_b")
    db.add_all([p2a, p2b])

    # Add statements
    s2a = Statement(id=generate_uuid(), dispute_id=d2_id, party_id=p2a.id,
                    position="The wall is 1 foot on my property", interest="Protect property value",
                    min_acceptable="Shared maintenance agreement", emotional_need="Acknowledgment of encroachment",
                    locked=True, submitted_at=datetime.now(timezone.utc))
    s2b = Statement(id=generate_uuid(), dispute_id=d2_id, party_id=p2b.id,
                    position="The wall has been here for 20 years", interest="Maintain status quo",
                    min_acceptable="50-50 cost sharing", emotional_need="Respect for longstanding arrangement",
                    locked=True, submitted_at=datetime.now(timezone.utc))
    db.add_all([s2a, s2b])

    # Add session
    sess2 = MediationSession(
        id=generate_uuid(), dispute_id=d2_id, session_type="ai_mediation", status="active",
        messages=[{"role": "mediator", "content": "Welcome. I have reviewed both perspectives on the shared wall dispute.",
                   "timestamp": datetime.now(timezone.utc).isoformat()}],
        ai_brief=json.dumps({"settlement_options": d2.settlement_options,
                             "recommended_opening": "Welcome to the joint session."})
    )
    db.add(sess2)
    print(f"  [OK] Dispute 2: {d2.title}")
    print(f"    Party A token: {p2a.session_token[:40]}...")
    print(f"    Party B token: {p2b.session_token[:40]}...")

    # ── Dispute 3: Resolved ─────────────────────────────────────────
    d3_id = generate_uuid()
    d3 = Dispute(id=d3_id, title="Tenant Security Deposit Return",
                 dispute_type="rent_tenancy", status="resolved",
                 arbitration_consent=False, round_count=4, risk_score=38.0)
    db.add(d3)
    p3a = Party(id=generate_uuid(), dispute_id=d3_id, role="party_a",
                name="Priya Nair", has_submitted_statement=True, has_signed_agreement=True,
                language="en")
    p3b = Party(id=generate_uuid(), dispute_id=d3_id, role="party_b",
                name="Vikram Reddy", has_submitted_statement=True, has_signed_agreement=True,
                language="en")
    db.add_all([p3a, p3b])
    print(f"  [OK] Dispute 3: {d3.title} (Resolved)")

    # ── Dispute 4: Escalated to Arbitration ─────────────────────────
    d4_id = generate_uuid()
    d4 = Dispute(id=d4_id, title="Contract Breach — IT Services",
                 dispute_type="contract_breach", status="escalated_arbitration",
                 arbitration_consent=True, round_count=3, risk_score=88.5,
                 escalation_reason="Parties unable to agree after 3 rounds")
    db.add(d4)
    p4a = Party(id=generate_uuid(), dispute_id=d4_id, role="party_a",
                name="TechSolutions Pvt Ltd", has_submitted_statement=True,
                language="en", arbitration_consent=True)
    p4b = Party(id=generate_uuid(), dispute_id=d4_id, role="party_b",
                name="CloudServices Inc", has_submitted_statement=True,
                language="en", arbitration_consent=True)
    db.add_all([p4a, p4b])
    print(f"  [OK] Dispute 4: {d4.title} (Escalated)")

    # ── Seed Arbitrators ────────────────────────────────────────────
    arbitrators = [
        Arbitrator(id=generate_uuid(), name="Adv. Meera Krishnamurthy",
                   email="meera@arbitration.in", bar_registration="KAR/ARB/2019/1234",
                   specializations=["property_boundary", "property_ownership", "rent_tenancy"],
                   languages=["en", "kn", "hi"], available=True, cases_assigned=2),
        Arbitrator(id=generate_uuid(), name="Adv. Sanjay Deshmukh",
                   email="sanjay@arbitration.in", bar_registration="MH/ARB/2020/5678",
                   specializations=["money_loan", "contract_breach", "employment"],
                   languages=["en", "hi", "mr"], available=True, cases_assigned=1),
        Arbitrator(id=generate_uuid(), name="Adv. Lakshmi Venkataraman",
                   email="lakshmi@arbitration.in", bar_registration="TN/ARB/2018/9012",
                   specializations=["consumer", "contract_breach", "other_civil"],
                   languages=["en", "ta", "hi"], available=True, cases_assigned=0),
        Arbitrator(id=generate_uuid(), name="Adv. Arjun Bhatt",
                   email="arjun@arbitration.in", bar_registration="GJ/ARB/2021/3456",
                   specializations=["family_inheritance", "property_ownership", "money_loan"],
                   languages=["en", "gu", "hi"], available=True, cases_assigned=1),
        Arbitrator(id=generate_uuid(), name="Adv. Fatima Begum",
                   email="fatima@arbitration.in", bar_registration="DL/ARB/2022/7890",
                   specializations=["employment", "consumer", "neighbourhood"],
                   languages=["en", "hi", "bn"], available=True, cases_assigned=0),
    ]
    db.add_all(arbitrators)
    print(f"\n  [OK] Seeded {len(arbitrators)} arbitrators")

    # ══════════════════════════════════════════════════════════════════════════
    # PREVENTION ENGINE — Civic Events + Risk Scores
    # ══════════════════════════════════════════════════════════════════════════

    print("\n[SEED] Seeding Prevention Engine data...\n")

    now = datetime.now(timezone.utc)

    # ── Demo Party: High Risk Property in Bengaluru ─────────────────
    high_risk_id = "PROP-BLR-2024-78901"
    civic_events_high = [
        CivicEvent(id=generate_uuid(), event_type="rera_complaint",
                   party_identifier=high_risk_id, source="rera",
                   event_date=now - timedelta(days=120),
                   district="Bengaluru Urban", state="Karnataka",
                   event_metadata={"complaint_no": "RERA/KA/2024/456", "type": "delayed_possession"}),
        CivicEvent(id=generate_uuid(), event_type="land_mutation_rejection",
                   party_identifier=high_risk_id, source="land_registry",
                   event_date=now - timedelta(days=90),
                   district="Bengaluru Urban", state="Karnataka",
                   event_metadata={"rejection_reason": "disputed_ownership", "survey_no": "45/2A"}),
        CivicEvent(id=generate_uuid(), event_type="cpgrams_escalation",
                   party_identifier=high_risk_id, source="cpgrams",
                   event_date=now - timedelta(days=60),
                   district="Bengaluru Urban", state="Karnataka",
                   event_metadata={"grievance_id": "CPG/2024/12345", "category": "land_dispute"}),
        CivicEvent(id=generate_uuid(), event_type="cersai_flag",
                   party_identifier=high_risk_id, source="cersai",
                   event_date=now - timedelta(days=30),
                   district="Bengaluru Urban", state="Karnataka",
                   event_metadata={"flag_type": "multiple_registrations", "asset_id": "CERSAI/78901"}),
        CivicEvent(id=generate_uuid(), event_type="rera_delay_notice",
                   party_identifier=high_risk_id, source="rera",
                   event_date=now - timedelta(days=15),
                   district="Bengaluru Urban", state="Karnataka",
                   event_metadata={"notice_type": "final_warning", "project": "Green Valley Phase 2"}),
    ]
    db.add_all(civic_events_high)

    risk_high = RiskScore(
        id=generate_uuid(), party_identifier=high_risk_id,
        score=84.3, dispute_type_predicted="property_ownership",
        nudge_sent=True, nudge_language="kn",
        nudge_message="⚠️ ನ್ಯಾಯAI ಎಚ್ಚರಿಕೆ: ನಿಮ್ಮ ಆಸ್ತಿಗೆ ವಿವಾದ ಸಂಕೇತಗಳು ಪತ್ತೆಯಾಗಿವೆ। ಅಪಾಯ ಸ್ಕೋರ್: 84.3/100.",
        computed_at=now - timedelta(days=5),
    )
    db.add(risk_high)
    print(f"  [OK] High-risk property: {high_risk_id} (score: 84.3, nudge sent)")

    # ── Demo Party: Medium Risk in Mumbai ───────────────────────────
    med_risk_id = "PROP-MUM-2024-34567"
    civic_events_med = [
        CivicEvent(id=generate_uuid(), event_type="rera_complaint",
                   party_identifier=med_risk_id, source="rera",
                   event_date=now - timedelta(days=150),
                   district="Mumbai", state="Maharashtra",
                   event_metadata={"complaint_no": "RERA/MH/2024/789", "type": "quality_issue"}),
        CivicEvent(id=generate_uuid(), event_type="cpgrams_escalation",
                   party_identifier=med_risk_id, source="cpgrams",
                   event_date=now - timedelta(days=80),
                   district="Mumbai", state="Maharashtra",
                   event_metadata={"grievance_id": "CPG/2024/67890", "category": "consumer_complaint"}),
    ]
    db.add_all(civic_events_med)

    risk_med = RiskScore(
        id=generate_uuid(), party_identifier=med_risk_id,
        score=56.7, dispute_type_predicted="consumer",
        nudge_sent=False,
        computed_at=now - timedelta(days=3),
    )
    db.add(risk_med)
    print(f"  [OK] Medium-risk property: {med_risk_id} (score: 56.7, no nudge)")

    # ── Demo Party: Low Risk in Chennai ─────────────────────────────
    low_risk_id = "PROP-CHN-2024-11223"
    civic_events_low = [
        CivicEvent(id=generate_uuid(), event_type="property_tax_dispute",
                   party_identifier=low_risk_id, source="municipal",
                   event_date=now - timedelta(days=200),
                   district="Chennai", state="Tamil Nadu",
                   event_metadata={"tax_year": "2023-24", "amount_disputed": 15000}),
    ]
    db.add_all(civic_events_low)

    risk_low = RiskScore(
        id=generate_uuid(), party_identifier=low_risk_id,
        score=22.1, dispute_type_predicted="other_civil",
        nudge_sent=False,
        computed_at=now - timedelta(days=10),
    )
    db.add(risk_low)
    print(f"  [OK] Low-risk property: {low_risk_id} (score: 22.1, no nudge)")

    # ── Additional civic events for demo variety ────────────────────
    extra_events = [
        CivicEvent(id=generate_uuid(), event_type="rera_complaint",
                   party_identifier="PROP-DEL-2024-55678", source="rera",
                   event_date=now - timedelta(days=45),
                   district="South Delhi", state="Delhi",
                   event_metadata={"type": "delayed_possession"}),
        CivicEvent(id=generate_uuid(), event_type="land_mutation_rejection",
                   party_identifier="PROP-DEL-2024-55678", source="land_registry",
                   event_date=now - timedelta(days=20),
                   district="South Delhi", state="Delhi",
                   event_metadata={"rejection_reason": "missing_documents"}),
        CivicEvent(id=generate_uuid(), event_type="encumbrance_certificate_issue",
                   party_identifier="PROP-HYD-2024-99012", source="land_registry",
                   event_date=now - timedelta(days=100),
                   district="Hyderabad", state="Telangana",
                   event_metadata={"issue_type": "prior_lien_detected"}),
    ]
    db.add_all(extra_events)
    print(f"  [OK] Seeded {len(civic_events_high) + len(civic_events_med) + len(civic_events_low) + len(extra_events)} civic events")
    print(f"  [OK] Seeded 3 risk score records")

    db.commit()
    db.close()

    print("\n[DONE] Database seeded successfully!")
    print("   Run: python run.py")


if __name__ == "__main__":
    seed()
