"""
NyayaAI — Synthetic Training Data Generator
Generates 5000 civic event sequences for LightGBM risk scorer training.

Labels:
  1 = dispute filed within 6 months of event sequence
  0 = no dispute filed

Sources simulated: RERA, CPGrams, Land Registry, CERSAI
"""

import csv
import random
import os
from datetime import datetime, timedelta

random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "training_data.csv")

EVENT_TYPES = [
    "rera_complaint", "land_mutation_rejection", "cpgrams_escalation",
    "cersai_flag", "rera_delay_notice", "property_tax_dispute",
    "encumbrance_certificate_issue", "building_violation_notice",
    "water_supply_complaint", "electricity_dispute"
]

DISPUTE_TYPES = [
    "property_boundary", "property_ownership", "rent_tenancy",
    "money_loan", "contract_breach", "employment", "consumer",
    "family_inheritance", "neighbourhood", "other_civil"
]

STATES = [
    "Karnataka", "Maharashtra", "Tamil Nadu", "Delhi", "Uttar Pradesh",
    "Gujarat", "Rajasthan", "Kerala", "West Bengal", "Telangana",
    "Andhra Pradesh", "Madhya Pradesh", "Punjab", "Haryana", "Bihar"
]

DISTRICTS = {
    "Karnataka": ["Bengaluru Urban", "Mysuru", "Mangaluru", "Hubli-Dharwad", "Belagavi"],
    "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik", "Thane"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem", "Tiruchirappalli"],
    "Delhi": ["Central Delhi", "South Delhi", "North Delhi", "East Delhi", "West Delhi"],
    "Uttar Pradesh": ["Lucknow", "Noida", "Agra", "Varanasi", "Kanpur"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Gandhinagar"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer"],
    "Kerala": ["Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Kannur"],
    "West Bengal": ["Kolkata", "Howrah", "Siliguri", "Durgapur", "Asansol"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Khammam"],
    "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Tirupati", "Nellore"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Jabalpur", "Gwalior", "Ujjain"],
    "Punjab": ["Chandigarh", "Ludhiana", "Amritsar", "Jalandhar", "Patiala"],
    "Haryana": ["Gurugram", "Faridabad", "Panipat", "Ambala", "Karnal"],
    "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Darbhanga"],
}


def generate_positive_sample():
    """Generate a high-risk civic event sequence that leads to a dispute."""
    state = random.choice(STATES)
    district = random.choice(DISTRICTS[state])
    party_id = f"PID-{random.randint(10000, 99999)}"

    # High-risk: more events, shorter gaps, multi-portal
    num_events = random.randint(3, 8)
    base_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 180))

    events = []
    sources_used = set()
    current_date = base_date

    for _ in range(num_events):
        event_type = random.choice(EVENT_TYPES)
        source = event_type.split("_")[0] if event_type.startswith("rera") else random.choice(["cpgrams", "land_registry", "cersai", "municipal"])
        sources_used.add(source)
        events.append({
            "event_type": event_type,
            "source": source,
            "date": current_date
        })
        # Short gaps for high-risk
        current_date += timedelta(days=random.randint(3, 25))

    return _extract_features(events, sources_used, state, district, party_id, label=1)


def generate_negative_sample():
    """Generate a low-risk civic event sequence that does NOT lead to a dispute."""
    state = random.choice(STATES)
    district = random.choice(DISTRICTS[state])
    party_id = f"PID-{random.randint(10000, 99999)}"

    # Low-risk: fewer events, longer gaps, single portal
    num_events = random.randint(1, 3)
    base_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 300))

    events = []
    sources_used = set()
    current_date = base_date

    for _ in range(num_events):
        event_type = random.choice(EVENT_TYPES)
        source = event_type.split("_")[0] if event_type.startswith("rera") else random.choice(["cpgrams", "land_registry", "cersai", "municipal"])
        sources_used.add(source)
        events.append({
            "event_type": event_type,
            "source": source,
            "date": current_date
        })
        # Longer gaps for low-risk
        current_date += timedelta(days=random.randint(30, 90))

    return _extract_features(events, sources_used, state, district, party_id, label=0)


def _extract_features(events, sources_used, state, district, party_id, label):
    """Extract the 9 LightGBM features from an event sequence."""
    now = events[-1]["date"] + timedelta(days=random.randint(1, 30))

    rera_count = sum(1 for e in events if "rera" in e["event_type"])
    mutation_count = sum(1 for e in events if "mutation" in e["event_type"])
    cpgrams_count = sum(1 for e in events if "cpgrams" in e["event_type"])
    cersai_count = sum(1 for e in events if "cersai" in e["event_type"])

    # Days between events
    if len(events) > 1:
        gaps = [(events[i+1]["date"] - events[i]["date"]).days for i in range(len(events)-1)]
        avg_days_between = sum(gaps) / len(gaps)
    else:
        avg_days_between = 999

    # Events in last 30/60 days
    events_last_30 = sum(1 for e in events if (now - e["date"]).days <= 30)
    events_last_60 = sum(1 for e in events if (now - e["date"]).days <= 60)

    # Multi-portal escalation score
    multi_portal_score = len(sources_used) / 5.0  # normalize to 0-1

    # Dispute type prediction based on event types
    if rera_count > 0 or mutation_count > 0:
        predicted_type = random.choice(["property_boundary", "property_ownership", "rent_tenancy"])
    elif cpgrams_count > 0:
        predicted_type = random.choice(["consumer", "neighbourhood", "other_civil"])
    else:
        predicted_type = random.choice(DISPUTE_TYPES)

    return {
        "party_identifier": party_id,
        "event_count": len(events),
        "rera_complaint_count": rera_count,
        "mutation_rejection_count": mutation_count,
        "cpgrams_escalation_count": cpgrams_count,
        "cersai_flag_count": cersai_count,
        "avg_days_between_events": round(avg_days_between, 1),
        "multi_portal_escalation_score": round(multi_portal_score, 3),
        "events_last_30_days": events_last_30,
        "events_last_60_days": events_last_60,
        "state": state,
        "district": district,
        "predicted_dispute_type": predicted_type,
        "label": label
    }


def generate_dataset(n_samples=5000):
    """Generate balanced dataset."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    samples = []
    n_positive = int(n_samples * 0.4)  # 40% positive (dispute filed)
    n_negative = n_samples - n_positive

    print(f"[GENERATE] Creating {n_samples} samples ({n_positive} positive, {n_negative} negative)...")

    for _ in range(n_positive):
        samples.append(generate_positive_sample())

    for _ in range(n_negative):
        samples.append(generate_negative_sample())

    random.shuffle(samples)

    # Write CSV
    fieldnames = list(samples[0].keys())
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(samples)

    print(f"[DONE] Saved to {OUTPUT_FILE}")
    print(f"  Positive (dispute): {n_positive}")
    print(f"  Negative (no dispute): {n_negative}")
    return OUTPUT_FILE


if __name__ == "__main__":
    generate_dataset()
