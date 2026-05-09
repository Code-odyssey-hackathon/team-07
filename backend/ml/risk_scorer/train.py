"""
NyayaAI — LightGBM Risk Scorer Training
Trains a LightGBM classifier on synthetic civic event data.

Target: ROC-AUC > 0.78 | Precision > 0.72 | Recall > 0.80
Output: ml/models/risk_scorer.pkl
"""

import os
import sys
import pandas as pd
import numpy as np
import joblib
import lightgbm as lgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score,
    classification_report, confusion_matrix
)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "training_data.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_FILE = os.path.join(MODEL_DIR, "risk_scorer.pkl")

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


def train():
    """Train LightGBM risk scorer and save model."""
    print("=" * 60)
    print("  NyayaAI — LightGBM Risk Scorer Training")
    print("=" * 60)

    # Check data exists
    if not os.path.exists(DATA_FILE):
        print(f"\n[ERROR] Training data not found at: {DATA_FILE}")
        print("  Run: python ml/risk_scorer/generate_training_data.py")
        sys.exit(1)

    # Load data
    print(f"\n[1/5] Loading training data from {DATA_FILE}...")
    df = pd.read_csv(DATA_FILE)
    print(f"  Samples: {len(df)}")
    print(f"  Positive (dispute): {df['label'].sum()}")
    print(f"  Negative (no dispute): {(df['label'] == 0).sum()}")
    print(f"  Positive rate: {df['label'].mean():.2%}")

    # Prepare features
    X = df[FEATURE_COLUMNS].values
    y = df["label"].values

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\n[2/5] Split: {len(X_train)} train / {len(X_test)} test")

    # LightGBM parameters
    params = {
        "objective": "binary",
        "metric": "auc",
        "boosting_type": "gbdt",
        "num_leaves": 31,
        "learning_rate": 0.05,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "verbose": -1,
        "n_estimators": 200,
        "max_depth": 6,
        "min_child_samples": 20,
        "reg_alpha": 0.1,
        "reg_lambda": 0.1,
        "random_state": 42,
    }

    # Train
    print(f"\n[3/5] Training LightGBM...")
    model = lgb.LGBMClassifier(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[lgb.log_evaluation(period=50)],
    )

    # Evaluate
    print(f"\n[4/5] Evaluation:")
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)

    roc_auc = roc_auc_score(y_test, y_pred_proba)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)

    print(f"\n  {'Metric':<20} {'Value':<10} {'Target':<10} {'Status':<8}")
    print(f"  {'-'*48}")
    print(f"  {'ROC-AUC':<20} {roc_auc:<10.4f} {'>0.78':<10} {'PASS' if roc_auc > 0.78 else 'FAIL'}")
    print(f"  {'Precision':<20} {precision:<10.4f} {'>0.72':<10} {'PASS' if precision > 0.72 else 'FAIL'}")
    print(f"  {'Recall':<20} {recall:<10.4f} {'>0.80':<10} {'PASS' if recall > 0.80 else 'FAIL'}")

    print(f"\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["No Dispute", "Dispute Filed"]))

    # Feature importance
    print(f"  Feature Importance:")
    importances = model.feature_importances_
    for name, imp in sorted(zip(FEATURE_COLUMNS, importances), key=lambda x: -x[1]):
        bar = "#" * int(imp / max(importances) * 30)
        print(f"    {name:<35} {imp:>4d}  {bar}")

    # Cross-validation
    print(f"\n  5-Fold Cross-Validation ROC-AUC:")
    cv_scores = cross_val_score(
        lgb.LGBMClassifier(**params), X, y,
        cv=5, scoring="roc_auc", n_jobs=-1
    )
    print(f"    Mean: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    print(f"    Folds: {[f'{s:.4f}' for s in cv_scores]}")

    # Save model
    print(f"\n[5/5] Saving model...")
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_FILE)
    print(f"  Saved to: {MODEL_FILE}")
    print(f"  Model size: {os.path.getsize(MODEL_FILE) / 1024:.1f} KB")

    print(f"\n{'=' * 60}")
    print(f"  Training Complete!")
    print(f"  ROC-AUC: {roc_auc:.4f} | Precision: {precision:.4f} | Recall: {recall:.4f}")
    print(f"{'=' * 60}")

    return model


if __name__ == "__main__":
    train()
