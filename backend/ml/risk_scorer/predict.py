"""
NyayaAI — LightGBM Risk Scorer Prediction
Loads the trained model and predicts risk scores from civic event data.
"""

import os
import logging
import joblib
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger("madhyastha.risk_scorer")

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_FILE = os.path.join(BASE_DIR, "models", "risk_scorer.pkl")

# Lazy-loaded model
_model = None


@dataclass
class RiskPrediction:
    risk_score: float          # 0-100
    dispute_probability: float # 0-1 raw probability
    predicted_dispute_type: str
    nudge_recommended: bool
    feature_breakdown: Dict


DISPUTE_TYPE_MAP = {
    "rera": ["property_boundary", "property_ownership", "rent_tenancy"],
    "land": ["property_boundary", "property_ownership"],
    "cpgrams": ["consumer", "neighbourhood", "other_civil"],
    "cersai": ["money_loan", "property_ownership"],
    "default": ["other_civil"],
}


def _load_model():
    """Lazy-load the trained LightGBM model."""
    global _model
    if _model is not None:
        return _model

    if not os.path.exists(MODEL_FILE):
        logger.warning(f"Risk scorer model not found at {MODEL_FILE}. Using mock scorer.")
        return None

    try:
        _model = joblib.load(MODEL_FILE)
        logger.info(f"Risk scorer model loaded from {MODEL_FILE}")
        return _model
    except Exception as e:
        logger.error(f"Failed to load risk scorer: {e}")
        return None


def _predict_dispute_type(events: List[Dict]) -> str:
    """Predict most likely dispute type from event types."""
    type_counts = {}
    for e in events:
        event_type = e.get("event_type", "").lower()
        for key, types in DISPUTE_TYPE_MAP.items():
            if key in event_type:
                for t in types:
                    type_counts[t] = type_counts.get(t, 0) + 1

    if type_counts:
        return max(type_counts, key=type_counts.get)
    return "other_civil"


def predict_risk(events: List[Dict], nudge_threshold: int = 72) -> RiskPrediction:
    """
    Predict dispute risk score from civic events.

    Args:
        events: List of civic event dicts with keys: event_type, source, event_date
        nudge_threshold: Score above which nudge is recommended (default: 72)

    Returns:
        RiskPrediction with score, type, and nudge recommendation.
    """
    # Import here to avoid circular imports
    from ml.risk_scorer.features import extract_features, features_to_array

    # Extract features
    features = extract_features(events)
    feature_array = features_to_array(features)

    # Load model
    model = _load_model()

    if model is not None:
        # Real prediction
        import numpy as np
        X = np.array([feature_array])
        prob = model.predict_proba(X)[0][1]
        risk_score = round(prob * 100, 1)
    else:
        # Mock prediction fallback
        risk_score = _mock_score(features)
        prob = risk_score / 100.0

    predicted_type = _predict_dispute_type(events)
    nudge_recommended = risk_score >= nudge_threshold

    return RiskPrediction(
        risk_score=risk_score,
        dispute_probability=round(prob, 4),
        predicted_dispute_type=predicted_type,
        nudge_recommended=nudge_recommended,
        feature_breakdown=features,
    )


def _mock_score(features: Dict) -> float:
    """Fallback mock scorer when model is not available."""
    score = 20.0
    score += features.get("event_count", 0) * 8
    score += features.get("rera_complaint_count", 0) * 12
    score += features.get("mutation_rejection_count", 0) * 15
    score += features.get("cpgrams_escalation_count", 0) * 10
    score += features.get("cersai_flag_count", 0) * 8
    score += features.get("multi_portal_escalation_score", 0) * 20
    score += features.get("events_last_30_days", 0) * 5

    avg_gap = features.get("avg_days_between_events", 999)
    if avg_gap < 15:
        score += 15
    elif avg_gap < 30:
        score += 8

    return min(max(round(score, 1), 0), 100)


def get_model_info() -> Dict:
    """Get info about the loaded model."""
    model = _load_model()
    if model is None:
        return {"status": "not_loaded", "using_mock": True}

    return {
        "status": "loaded",
        "using_mock": False,
        "model_path": MODEL_FILE,
        "model_type": "LightGBM",
        "n_estimators": model.n_estimators,
        "num_features": model.n_features_in_,
    }
