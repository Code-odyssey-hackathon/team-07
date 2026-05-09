"""
NyayaAI — Feature Engineering for Risk Scorer
Extracts the 9 input features from raw civic event data for LightGBM prediction.
"""

from typing import List, Dict
from datetime import datetime


FEATURE_COLUMNS = [
    "event_count",
    "rera_complaint_count",
    "mutation_rejection_count",
    "cpgrams_escalation_count",
    "cersai_flag_count",
    "avg_days_between_events",
    "multi_portal_escalation_score",
    "events_last_30_days",
    "events_last_60_days",
]


def extract_features(events: List[Dict], reference_date: datetime = None) -> Dict:
    """
    Extract LightGBM features from a list of civic events.

    Args:
        events: List of dicts with keys: event_type, source, event_date (str or datetime)
        reference_date: The date to compute recency from. Defaults to now.

    Returns:
        Dict with 9 feature values ready for model input.
    """
    if not events:
        return {col: 0 for col in FEATURE_COLUMNS}

    if reference_date is None:
        reference_date = datetime.utcnow()

    # Parse dates if needed
    parsed_events = []
    for e in events:
        event_date = e.get("event_date") or e.get("date")
        if isinstance(event_date, str):
            try:
                event_date = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                event_date = datetime.utcnow()
        parsed_events.append({
            "event_type": e.get("event_type", ""),
            "source": e.get("source", ""),
            "date": event_date
        })

    # Sort by date
    parsed_events.sort(key=lambda x: x["date"])

    # Count by type
    rera_count = sum(1 for e in parsed_events if "rera" in e["event_type"].lower())
    mutation_count = sum(1 for e in parsed_events if "mutation" in e["event_type"].lower())
    cpgrams_count = sum(1 for e in parsed_events if "cpgrams" in e["event_type"].lower())
    cersai_count = sum(1 for e in parsed_events if "cersai" in e["event_type"].lower())

    # Average days between events
    if len(parsed_events) > 1:
        gaps = []
        for i in range(len(parsed_events) - 1):
            delta = (parsed_events[i + 1]["date"] - parsed_events[i]["date"]).days
            gaps.append(max(delta, 0))
        avg_days_between = sum(gaps) / len(gaps)
    else:
        avg_days_between = 999.0

    # Events in last 30/60 days
    events_last_30 = sum(
        1 for e in parsed_events
        if (reference_date - e["date"]).days <= 30
    )
    events_last_60 = sum(
        1 for e in parsed_events
        if (reference_date - e["date"]).days <= 60
    )

    # Multi-portal escalation score
    sources = set(e["source"] for e in parsed_events if e["source"])
    multi_portal_score = min(len(sources) / 5.0, 1.0)

    return {
        "event_count": len(parsed_events),
        "rera_complaint_count": rera_count,
        "mutation_rejection_count": mutation_count,
        "cpgrams_escalation_count": cpgrams_count,
        "cersai_flag_count": cersai_count,
        "avg_days_between_events": round(avg_days_between, 1),
        "multi_portal_escalation_score": round(multi_portal_score, 3),
        "events_last_30_days": events_last_30,
        "events_last_60_days": events_last_60,
    }


def features_to_array(features: Dict) -> list:
    """Convert feature dict to ordered list for model input."""
    return [features[col] for col in FEATURE_COLUMNS]
