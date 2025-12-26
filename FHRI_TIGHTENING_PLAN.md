# FHRI Hallucination Detector Tightening Plan

## Overview
This document provides concrete implementation guidance for tightening the FHRI-based hallucination detector for the financial chatbot.

---

## ✅ **COMPLETED: Fact-Based Grounding (Objective 1)**

### Files Created:
1. **`src/numeric_validators.py`** - Numeric tolerance validation
   - Extracts numeric claims (price, %, EPS, revenue, market cap, P/E)
   - Validates against reference data with configurable tolerances
   - **Tolerances specified:**
     - Price: 5%
     - % change: 10%
     - Returns: 15%
     - EPS: 10%
     - Revenue: 10%
     - Market cap: 10%
     - P/E ratio: 15%
     - Dividend yield: 20%
     - Default: 10%

2. **`src/entity_validators.py`** - Entity & relation validation
   - Extracts entities (tickers, companies, people, dates)
   - Validates entity grounding in passages/API
   - Computes grounding penalties for ungrounded entities

### Changes to `src/fhri_scoring.py`:
- **Imported validators** (lines 30-43)
- **Enhanced `compute_grounding_score`** (lines 253-458):
  - Numeric validation with hard cap (G ~0.2 if any invalid)
  - Entity validation with downweighting
  - Fact penalty applied to all scoring paths (ONLINE, HYBRID, PASSAGES)

**Result:** For numeric claims, if any number is absent or mismatched beyond tolerance → **G capped at 0.2**. For non-numeric, missing entities → **aggressive downweight**.

---

## 🔧 **TODO: Numeric/Directional Hard Checks (Objective 2)**

### Changes needed in `src/fhri_scoring.py`:

**Location:** `compute_numerical_directional_score` method (starts ~line 460)

**Add after line 476 (inside numeric mode):**

```python
# HARD EXTERNAL CHECKS: Numeric validation
if multi_source_data and validate_all_numeric_claims:
    # Build reference data
    reference_data = {}
    finnhub_data = multi_source_data.get("finnhub_quote") or {}
    reference_data["price"] = finnhub_data.get("c") or finnhub_data.get("price")
    reference_data["pct_change"] = finnhub_data.get("dp")

    fundamentals = multi_source_data.get("fundamentals", {}).get("data", {}).get("metrics", {})
    reference_data.update(fundamentals)

    # Validate all numeric claims
    numeric_validation = validate_all_numeric_claims(answer, reference_data, require_all_valid=False)

    if numeric_validation["has_numeric_claims"]:
        accuracy_rate = numeric_validation["accuracy_rate"]

        # Hard check: If relative error > tolerance for ANY key numeric, set N/D ~0.1-0.2
        if numeric_validation["any_invalid"]:
            score = 0.15  # Hard penalty
            logger.warning(f"Numeric mismatch detected in N/D score: {numeric_validation['invalid_claims']}/{numeric_validation['validated_claims']} invalid")
            return score

        # Only assign high score (≥0.8) when ALL key numerics within tolerance
        if accuracy_rate >= 0.9:
            score = 0.88  # High confidence
            logger.info(f"All numeric claims validated: {numeric_validation['valid_claims']}/{numeric_validation['validated_claims']}")
            return score
```

---

## 🔧 **TODO: NLI Answer-vs-Evidence Integration (Objective 3)**

### New Helper: `src/nli_answer_evidence.py`

Create this file:

```python
# src/nli_answer_evidence.py
"""
NLI-based answer-vs-evidence contradiction scoring.

Uses NLI model to check if answer contradicts retrieved passages.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("nli_answer_evidence")


def compute_answer_evidence_nli(
    answer: str,
    passages: List[str],
    nli_detector,
    timeout: float = 5.0
) -> Dict[str, Any]:
    """
    Compute NLI scores between answer (hypothesis) and passages (premises).

    Args:
        answer: LLM-generated answer
        passages: Retrieved evidence passages
        nli_detector: LazyNLIDetector instance from detectors.py
        timeout: Timeout per NLI call (seconds)

    Returns:
        Dict with:
            - max_entailment: float (max entailment score across passages)
            - max_contradiction: float (max contradiction score across passages)
            - avg_entailment: float
            - avg_contradiction: float
            - passage_scores: List[Dict] with per-passage scores
    """
    if not passages or not answer:
        return {
            "max_entailment": 0.0,
            "max_contradiction": 0.0,
            "avg_entailment": 0.0,
            "avg_contradiction": 0.0,
            "passage_scores": []
        }

    if not nli_detector or not nli_detector.is_available():
        logger.warning("NLI detector not available, skipping answer-evidence scoring")
        return {
            "max_entailment": 0.0,
            "max_contradiction": 0.0,
            "avg_entailment": 0.0,
            "avg_contradiction": 0.0,
            "passage_scores": []
        }

    entailment_scores = []
    contradiction_scores = []
    passage_scores = []

    for idx, passage in enumerate(passages[:5]):  # Limit to top 5 passages to avoid timeout
        # Run NLI: premise=passage, hypothesis=answer
        try:
            result = nli_detector.compute_contradiction(
                premise=passage,
                hypothesis=answer,
                timeout=timeout,
                bidirectional=False  # Unidirectional: passage → answer
            )

            if result:
                # Result format: (contradiction_score, [entailment, neutral, contradiction], metadata)
                contradiction_score, probs, metadata = result
                entailment_score = probs[0]  # Entailment probability
                neutral_score = probs[1]
                contradiction_prob = probs[2]

                entailment_scores.append(entailment_score)
                contradiction_scores.append(contradiction_prob)

                passage_scores.append({
                    "passage_idx": idx,
                    "entailment": entailment_score,
                    "neutral": neutral_score,
                    "contradiction": contradiction_prob
                })

                logger.debug(f"Passage {idx}: entailment={entailment_score:.3f}, contradiction={contradiction_prob:.3f}")

        except Exception as e:
            logger.warning(f"NLI failed for passage {idx}: {e}")
            continue

    if not entailment_scores:
        return {
            "max_entailment": 0.0,
            "max_contradiction": 0.0,
            "avg_entailment": 0.0,
            "avg_contradiction": 0.0,
            "passage_scores": []
        }

    return {
        "max_entailment": max(entailment_scores),
        "max_contradiction": max(contradiction_scores),
        "avg_entailment": sum(entailment_scores) / len(entailment_scores),
        "avg_contradiction": sum(contradiction_scores) / len(contradiction_scores),
        "passage_scores": passage_scores
    }


def apply_nli_veto(
    fhri: float,
    nli_result: Dict[str, Any],
    scenario: str,
    veto_threshold: float = 0.7,
    high_risk_scenarios: set = {"numeric_kpi", "regulatory"}
) -> Tuple[float, bool, str]:
    """
    Apply NLI-based veto to FHRI score.

    For high-risk scenarios (numeric_kpi, regulatory), if contradiction ≥ veto_threshold,
    either veto (return 0) or downscale FHRI by (1 - contradiction).

    Args:
        fhri: Current FHRI score
        nli_result: Result from compute_answer_evidence_nli
        scenario: Detected scenario (e.g., "numeric_kpi")
        veto_threshold: Contradiction threshold for veto (default 0.7)
        high_risk_scenarios: Set of scenario IDs that trigger veto

    Returns:
        Tuple of (adjusted_fhri, vetoed, reason)
    """
    max_contradiction = nli_result.get("max_contradiction", 0.0)
    scenario_key = (scenario or "default").lower()

    if scenario_key not in high_risk_scenarios:
        # No veto for low-risk scenarios
        return (fhri, False, "")

    if max_contradiction >= veto_threshold:
        # VETO: Hard contradiction detected
        logger.warning(f"NLI veto triggered: max_contradiction={max_contradiction:.3f} ≥ {veto_threshold} for scenario={scenario_key}")
        # Option 1: Hard veto (return 0)
        # return (0.0, True, f"High contradiction detected ({max_contradiction:.2f})")

        # Option 2: Soft downscale (multiply by 1 - contradiction)
        adjusted_fhri = fhri * (1 - max_contradiction)
        return (adjusted_fhri, True, f"Downscaled by NLI contradiction ({max_contradiction:.2f})")

    elif max_contradiction >= 0.5:
        # Moderate contradiction: downscale FHRI slightly
        adjusted_fhri = fhri * (1 - max_contradiction * 0.5)
        return (adjusted_fhri, False, f"Moderate contradiction penalty ({max_contradiction:.2f})")

    return (fhri, False, "")
```

### Integration into `src/fhri_scoring.py`:

**Add import at top:**
```python
try:
    from nli_answer_evidence import compute_answer_evidence_nli, apply_nli_veto
except ImportError:
    try:
        from src.nli_answer_evidence import compute_answer_evidence_nli, apply_nli_veto
    except ImportError:
        logger.warning("NLI answer-evidence module not available")
        compute_answer_evidence_nli = None
        apply_nli_veto = None
```

**In `compute_fhri` method (around line 800), after computing base FHRI, add:**

```python
# NLI answer-vs-evidence check (Objective 3)
nli_answer_evidence_result = None
if compute_answer_evidence_nli:
    try:
        from detectors import get_nli_detector
        nli_detector = get_nli_detector()

        nli_answer_evidence_result = compute_answer_evidence_nli(
            answer=answer,
            passages=passages,
            nli_detector=nli_detector,
            timeout=5.0
        )

        logger.info(f"NLI answer-evidence: max_entailment={nli_answer_evidence_result['max_entailment']:.3f}, max_contradiction={nli_answer_evidence_result['max_contradiction']:.3f}")

        # Apply veto for high-risk scenarios
        if apply_nli_veto:
            fhri, vetoed, reason = apply_nli_veto(
                fhri=fhri,
                nli_result=nli_answer_evidence_result,
                scenario=scenario_key,
                veto_threshold=0.7,
                high_risk_scenarios=HIGH_RISK_SCENARIOS
            )

            if vetoed:
                logger.warning(f"FHRI adjusted by NLI veto: {reason}")

    except Exception as e:
        logger.exception(f"NLI answer-evidence check failed: {e}")
```

---

## 🔧 **TODO: Scenario-Specific Caps (Objective 4)**

### Changes to `src/fhri_scoring.py`:

**Add after computing FHRI and before applying boosts (around line 805):**

```python
# SCENARIO-SPECIFIC CAPS (Objective 4)
# For numeric_kpi/regulatory, cap FHRI (e.g., ≤0.3) when numeric_mismatch or no evidence
if scenario_key in ("numeric_kpi", "regulatory"):
    # Check numeric mismatch flag
    has_numeric_mismatch = False
    if multi_source_data and validate_all_numeric_claims:
        reference_data = {}
        finnhub_data = multi_source_data.get("finnhub_quote") or {}
        reference_data["price"] = finnhub_data.get("c") or finnhub_data.get("price")
        reference_data["pct_change"] = finnhub_data.get("dp")
        fundamentals = multi_source_data.get("fundamentals", {}).get("data", {}).get("metrics", {})
        reference_data.update(fundamentals)

        numeric_validation = validate_all_numeric_claims(answer, reference_data, require_all_valid=False)
        has_numeric_mismatch = numeric_validation.get("any_invalid", False)

    # Check if we have evidence (passages or multi-source)
    has_evidence = bool(passages or (multi_source_data and multi_source_data.get("sources_used")))

    # Apply cap
    if has_numeric_mismatch or not has_evidence:
        logger.warning(f"Scenario cap triggered for {scenario_key}: numeric_mismatch={has_numeric_mismatch}, has_evidence={has_evidence}")
        fhri = min(fhri, 0.3)  # Hard cap at 0.3

elif scenario_key in ("definition", "education", "advice"):
    # Looser thresholds for low-risk scenarios
    # No cap applied
    pass
```

---

## 🔧 **TODO: Entropy as Modulator (Objective 5)**

### Changes to `src/fhri_scoring.py`:

**Replace the current entropy handling (around line 785) with:**

```python
# ENTROPY AS MODULATOR (Objective 5)
# If G/N/D low and entropy high, push FHRI further down
# If G/N/D high but entropy high, shave FHRI slightly

if E_val is not None:
    G_val = subscores.get("G", 0.0)
    N_val = subscores.get("N_or_D", 0.0)

    # Compute average of G and N/D
    gn_avg = (G_val + N_val) / 2.0 if (G_val is not None and N_val is not None) else 0.5

    if gn_avg < 0.4 and E_val < 0.4:
        # Low G/N/D + High entropy → push FHRI down further
        entropy_penalty = 0.85  # 15% penalty
        fhri = fhri * entropy_penalty
        logger.info(f"Entropy modulator (low G/N/D + high entropy): FHRI *= {entropy_penalty:.2f}")

    elif gn_avg > 0.7 and E_val < 0.6:
        # High G/N/D but moderate-high entropy → shave FHRI slightly
        entropy_penalty = 0.95  # 5% penalty
        fhri = fhri * entropy_penalty
        logger.info(f"Entropy modulator (high G/N/D + moderate entropy): FHRI *= {entropy_penalty:.2f}")
```

---

## 🔧 **TODO: Calibration Script (Objective 6)**

### Create: `scripts/calibrate_fhri.py`

```python
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

    print(f"\nOptimal threshold: {best_threshold:.3f}")
    print(f"\nClassification Report:")
    print(classification_report(y, y_pred, target_names=["Accurate", "Hallucination"]))

    print(f"\nConfusion Matrix:")
    print(confusion_matrix(y, y_pred))

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
        help="Path to labeled evaluation dataset"
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

    train_calibration_model(
        dataset_path=args.dataset,
        output_model_path=args.output,
        threshold_metric=args.metric
    )


if __name__ == "__main__":
    main()
```

**Usage:**
```bash
python scripts/calibrate_fhri.py --dataset data/evaluation_dataset.json --output models/fhri_calibration.pkl --metric recall
```

---

## 🔧 **TODO: Evaluation Sweep Enhancements (Objective 7)**

### Changes to `scripts/evaluate_detection.py`:

**Add new evaluation modes and threshold sweep:**

```python
# Add after line 670 (in main function):

# THRESHOLD SWEEP MODE
parser.add_argument(
    "--sweep",
    action="store_true",
    help="Run threshold sweep (test multiple FHRI thresholds)"
)
parser.add_argument(
    "--sweep_range",
    type=str,
    default="0.3,0.4,0.5,0.6,0.7,0.8,0.9",
    help="Comma-separated list of thresholds to sweep"
)
parser.add_argument(
    "--per_scenario",
    action="store_true",
    help="Report per-scenario breakdown in results"
)
parser.add_argument(
    "--compare_baselines",
    action="store_true",
    help="Compare baseline methods (entropy-only, G-only, numeric-only)"
)

# ... (after args = parser.parse_args())

if args.sweep:
    # Threshold sweep mode
    thresholds = [float(t) for t in args.sweep_range.split(",")]
    print(f"\n🔍 Running threshold sweep: {thresholds}")

    sweep_results = []
    for threshold in thresholds:
        print(f"\n{'='*60}")
        print(f"Testing threshold: {threshold:.2f}")
        print(f"{'='*60}")

        evaluator = DetectionEvaluator(
            backend_url=args.backend,
            hallu_threshold=args.threshold,
            fhri_threshold=threshold,
            use_static_answers=args.use_static_answers
        )
        evaluator.use_fhri = use_fhri
        results = evaluator.evaluate_dataset(args.dataset)

        if results:
            metrics = evaluator.calculate_metrics()
            sweep_results.append({
                "threshold": threshold,
                "metrics": metrics
            })

            # Print summary
            hallucination_metrics = metrics.get("hallucination", {})
            print(f"\n📊 Threshold {threshold:.2f} Results:")
            print(f"  Hallucination Recall: {hallucination_metrics.get('recall', 0):.2%}")
            print(f"  Hallucination Precision: {hallucination_metrics.get('precision', 0):.2%}")
            print(f"  Hallucination F1: {hallucination_metrics.get('f1_score', 0):.4f}")
            print(f"  Overall Accuracy: {metrics['overall']['accuracy']:.2%}")

    # Save sweep results
    sweep_output = args.output.replace(".json", "_sweep.json")
    with open(sweep_output, 'w') as f:
        json.dump({"sweep_results": sweep_results}, f, indent=2)
    print(f"\n✓ Sweep results saved to {sweep_output}")

    # Find best threshold
    best_threshold = max(sweep_results, key=lambda x: x["metrics"].get("hallucination", {}).get("f1_score", 0))
    print(f"\n🏆 Best threshold: {best_threshold['threshold']:.2f} (F1={best_threshold['metrics']['hallucination']['f1_score']:.4f})")

    sys.exit(0)

# PER-SCENARIO BREAKDOWN
if args.per_scenario:
    # Group results by scenario
    from collections import defaultdict
    scenario_results = defaultdict(list)

    for result in results:
        scenario = result.get("scenario_detected", "default")
        scenario_results[scenario].append(result)

    print(f"\n{'='*60}")
    print("PER-SCENARIO BREAKDOWN")
    print(f"{'='*60}")

    for scenario, scenario_samples in scenario_results.items():
        correct = sum(1 for r in scenario_samples if r["correct"])
        total = len(scenario_samples)
        accuracy = correct / total if total > 0 else 0.0

        print(f"\n{scenario.upper()}: {correct}/{total} correct ({accuracy:.2%})")

        # Calculate per-scenario metrics for hallucination detection
        scenario_tp = sum(1 for r in scenario_samples if r["true_label"] == "hallucination" and r["predicted_label"] == "hallucination")
        scenario_fp = sum(1 for r in scenario_samples if r["true_label"] != "hallucination" and r["predicted_label"] == "hallucination")
        scenario_fn = sum(1 for r in scenario_samples if r["true_label"] == "hallucination" and r["predicted_label"] != "hallucination")

        scenario_precision = scenario_tp / (scenario_tp + scenario_fp) if (scenario_tp + scenario_fp) > 0 else 0.0
        scenario_recall = scenario_tp / (scenario_tp + scenario_fn) if (scenario_tp + scenario_fn) > 0 else 0.0
        scenario_f1 = 2 * (scenario_precision * scenario_recall) / (scenario_precision + scenario_recall) if (scenario_precision + scenario_recall) > 0 else 0.0

        print(f"  Hallucination Detection - P: {scenario_precision:.3f}, R: {scenario_recall:.3f}, F1: {scenario_f1:.3f}")

# BASELINE COMPARISONS
if args.compare_baselines:
    print(f"\n{'='*60}")
    print("BASELINE COMPARISONS")
    print(f"{'='*60}")

    # Baseline 1: Entropy-only
    print("\n🔹 Baseline: Entropy-only")
    entropy_correct = sum(1 for r in results if (r["entropy"] is not None and r["entropy"] > args.threshold) == (r["true_label"] == "hallucination"))
    entropy_accuracy = entropy_correct / len(results) if results else 0.0
    print(f"  Accuracy: {entropy_accuracy:.2%}")

    # Baseline 2: G-only
    print("\n🔹 Baseline: Grounding-only")
    g_correct = sum(1 for r in results if (r["fhri_subscores"].get("G", 0) < 0.5) == (r["true_label"] == "hallucination"))
    g_accuracy = g_correct / len(results) if results else 0.0
    print(f"  Accuracy: {g_accuracy:.2%}")

    # Baseline 3: Numeric-only
    print("\n🔹 Baseline: Numeric-check-only")
    numeric_correct = sum(1 for r in results if (r.get("numeric_price_check", {}).get("is_mismatch", False)) == (r["true_label"] == "hallucination"))
    numeric_accuracy = numeric_correct / len(results) if results else 0.0
    print(f"  Accuracy: {numeric_accuracy:.2%}")
```

---

## 🧪 **Testing & Validation**

### Run Tests:

1. **Unit test validators:**
```bash
pytest tests/test_numeric_validators.py
pytest tests/test_entity_validators.py
```

2. **Integration test:**
```bash
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --mode fhri --use_static_answers
```

3. **Threshold sweep:**
```bash
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --sweep --sweep_range "0.3,0.5,0.7,0.9" --per_scenario
```

4. **Calibration:**
```bash
python scripts/calibrate_fhri.py --dataset data/evaluation_dataset.json --metric recall
```

---

## 📊 **Expected Improvements**

| Metric | Before | After (Expected) |
|--------|--------|------------------|
| Hallucination Recall | ~70% | **≥85%** |
| Hallucination Precision | ~60% | **≥75%** |
| False Positives (numeric) | High | **Low** (hard caps) |
| Grounding Quality | Similarity | **Fact-based** |
| Scenario Adherence | Weak | **Strong** (caps) |

---

## ✅ **Summary of Deliverables**

### Completed:
1. ✅ `src/numeric_validators.py` - Numeric tolerance checks
2. ✅ `src/entity_validators.py` - Entity grounding validation
3. ✅ Enhanced `src/fhri_scoring.py` - Fact-based grounding with hard caps

### To Implement:
4. ⏳ `src/nli_answer_evidence.py` - NLI answer-vs-evidence integration
5. ⏳ Enhanced N/D score with hard external checks
6. ⏳ Scenario-specific caps in `compute_fhri`
7. ⏳ Entropy modulator adjustments
8. ⏳ `scripts/calibrate_fhri.py` - Logistic regression calibration
9. ⏳ Enhanced `scripts/evaluate_detection.py` - Threshold sweep & baselines

---

**Next Steps:**
1. Review completed code (numeric/entity validators)
2. Implement remaining TODOs in sequence
3. Run evaluation sweep to validate improvements
4. Train calibration model on labeled dataset
5. Deploy to production with A/B testing

**Estimated Time:** 4-6 hours for full implementation + testing.
