#!/usr/bin/env python3
"""
Calibration script for FHRI using logistic regression.

Trains a small logistic regression on labeled evaluation set with features:
- G, N/D, T, C, E (sub-scores)
- numeric_mismatch_flag
- NLI contradiction/entailment scores
- scenario (one-hot encoded)

Outputs predicted probability as calibrated FHRI.
Chooses threshold via ROC/PR to maximize hallucination recall.

Usage:
    python scripts/calibrate_fhri.py --dataset data/evaluation_dataset.json --output models/fhri_calibration.pkl --metric recall
"""

import os
import sys
import json
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_recall_curve,
    roc_curve,
    auc,
    classification_report,
    confusion_matrix
)
import joblib

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def load_labeled_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """Load labeled evaluation dataset."""
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    return data.get("samples", [])


def extract_features(sample: Dict[str, Any], fhri_subscores: Dict[str, float]) -> np.ndarray:
    """
    Extract feature vector from sample.

    Features:
    - G, N_or_D, T, C, E (5 features)
    - numeric_mismatch_flag (1 feature)
    - NLI_contradiction, NLI_entailment (2 features)
    - scenario_one_hot (10 features for 10 scenarios)

    Total: 18 features
    """
    features = []

    # Sub-scores (fill missing with 0.5)
    features.append(fhri_subscores.get("G", 0.5))
    features.append(fhri_subscores.get("N_or_D", 0.5))
    features.append(fhri_subscores.get("T", 0.5))
    features.append(fhri_subscores.get("C", 0.5))
    features.append(fhri_subscores.get("E", 0.5))

    # Numeric mismatch flag (0 or 1)
    numeric_check = sample.get("numeric_price_check", {})
    features.append(1.0 if numeric_check.get("is_mismatch", False) else 0.0)

    # NLI scores (fill missing with 0.0)
    nli_result = sample.get("nli_answer_evidence", {})
    features.append(nli_result.get("max_contradiction", 0.0))
    features.append(nli_result.get("max_entailment", 0.0))

    # Scenario one-hot encoding
    scenario = sample.get("scenario_detected", "default").lower()
    scenarios = ["numeric_kpi", "intraday", "directional", "regulatory", "fundamentals",
                 "multi_ticker", "news", "crypto", "advice", "default"]
    for s in scenarios:
        features.append(1.0 if scenario == s else 0.0)

    return np.array(features)


def train_calibration_model(
    dataset_path: str,
    output_model_path: str = "models/fhri_calibration.pkl",
    threshold_metric: str = "f1"
) -> Dict[str, Any]:
    """
    Train logistic regression calibration model.

    Args:
        dataset_path: Path to labeled evaluation dataset
        output_model_path: Where to save trained model
        threshold_metric: Metric to optimize for threshold selection
                          ("f1", "recall", "precision")

    Returns:
        Dict with model, scaler, threshold, metrics
    """
    # Load dataset
    samples = load_labeled_dataset(dataset_path)

    # Extract features and labels
    X = []
    y = []

    for sample in samples:
        label = sample.get("ground_truth_label", "")
        if label not in ["accurate", "hallucination"]:
            continue  # Skip contradictions for now (binary classification)

        # Get FHRI subscores (assume they're computed and stored in sample)
        fhri_subscores = sample.get("fhri_subscores", {})

        features = extract_features(sample, fhri_subscores)
        X.append(features)

        # Binary label: 1 = hallucination, 0 = accurate
        y.append(1 if label == "hallucination" else 0)

    X = np.array(X)
    y = np.array(y)

    print(f"Training on {len(X)} samples ({np.sum(y)} hallucinations, {len(y) - np.sum(y)} accurate)")

    if len(X) == 0:
        print("❌ No samples available for training. Please ensure dataset has computed FHRI subscores.")
        return None

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train logistic regression
    model = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42)
    model.fit(X_scaled, y)

    # Get predicted probabilities
    y_proba = model.predict_proba(X_scaled)[:, 1]  # Probability of hallucination

    # Find optimal threshold using precision-recall curve
    precisions, recalls, thresholds_pr = precision_recall_curve(y, y_proba)

    if threshold_metric == "f1":
        f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-10)
        best_idx = np.argmax(f1_scores)
        best_threshold = thresholds_pr[best_idx] if best_idx < len(thresholds_pr) else 0.5
    elif threshold_metric == "recall":
        # Find threshold that gives recall ≥ 0.9
        target_recall = 0.9
        valid_idx = np.where(recalls >= target_recall)[0]
        if len(valid_idx) > 0:
            best_idx = valid_idx[0]
            best_threshold = thresholds_pr[best_idx] if best_idx < len(thresholds_pr) else 0.5
        else:
            best_threshold = 0.3  # Lower threshold for higher recall
    else:  # precision
        target_precision = 0.8
        valid_idx = np.where(precisions >= target_precision)[0]
        if len(valid_idx) > 0:
            best_idx = valid_idx[-1]  # Highest recall at target precision
            best_threshold = thresholds_pr[best_idx] if best_idx < len(thresholds_pr) else 0.5
        else:
            best_threshold = 0.7  # Higher threshold for higher precision

    # Evaluate
    y_pred = (y_proba >= best_threshold).astype(int)

    print(f"\n{'='*60}")
    print(f"CALIBRATION RESULTS")
    print(f"{'='*60}")
    print(f"\nOptimal threshold: {best_threshold:.3f}")
    print(f"\nClassification Report:")
    print(classification_report(y, y_pred, target_names=["Accurate", "Hallucination"]))

    print(f"\nConfusion Matrix:")
    cm = confusion_matrix(y, y_pred)
    print(f"                Predicted")
    print(f"                Accurate  Hallucination")
    print(f"Actual Accurate    {cm[0][0]:<6}  {cm[0][1]:<6}")
    print(f"       Hallucination {cm[1][0]:<6}  {cm[1][1]:<6}")

    # Save model
    os.makedirs(os.path.dirname(output_model_path), exist_ok=True)
    joblib.dump({
        "model": model,
        "scaler": scaler,
        "threshold": best_threshold,
        "feature_names": ["G", "N_or_D", "T", "C", "E", "numeric_mismatch", "NLI_contradiction", "NLI_entailment"] + [f"scenario_{s}" for s in ["numeric_kpi", "intraday", "directional", "regulatory", "fundamentals", "multi_ticker", "news", "crypto", "advice", "default"]]
    }, output_model_path)

    print(f"\n✓ Model saved to {output_model_path}")

    return {
        "model": model,
        "scaler": scaler,
        "threshold": best_threshold,
        "train_size": len(X),
        "hallucination_rate": np.mean(y)
    }


def main():
    parser = argparse.ArgumentParser(description="Calibrate FHRI using logistic regression")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/evaluation_dataset.json",
        help="Path to labeled evaluation dataset (must have FHRI subscores computed)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="models/fhri_calibration.pkl",
        help="Path to save calibration model"
    )
    parser.add_argument(
        "--metric",
        type=str,
        choices=["f1", "recall", "precision"],
        default="f1",
        help="Metric to optimize for threshold selection"
    )

    args = parser.parse_args()

    # Check if dataset exists
    if not os.path.exists(args.dataset):
        print(f"❌ Dataset not found: {args.dataset}")
        print("\nPlease provide a labeled dataset with FHRI subscores computed.")
        print("You can generate this by running:")
        print(f"  python scripts/evaluate_detection.py --dataset {args.dataset} --use_static_answers --mode fhri")
        sys.exit(1)

    train_calibration_model(
        dataset_path=args.dataset,
        output_model_path=args.output,
        threshold_metric=args.metric
    )


if __name__ == "__main__":
    main()
