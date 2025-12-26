"""
Scenario-based FHRI Evaluation Script

Extends the base evaluation to group results by detected scenario and compute
per-scenario metrics comparing entropy-only vs FHRI detection.

Usage:
    python scripts/evaluate_by_scenario.py --report results/evaluation_report.json --output results/scenario_analysis.json
"""

import os
import sys
import json
import argparse
from collections import defaultdict
from typing import Dict, List, Any
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def load_evaluation_report(report_path: str) -> Dict[str, Any]:
    """Load evaluation report JSON."""
    with open(report_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def group_by_scenario(detailed_results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group evaluation results by detected scenario."""
    scenario_groups = defaultdict(list)

    for result in detailed_results:
        # Get scenario from meta (if available)
        scenario = result.get("scenario_detected", "default")
        if not scenario:
            scenario = "default"
        scenario_groups[scenario].append(result)

    return dict(scenario_groups)


def calculate_metrics_for_group(results: List[Dict[str, Any]],
                                  use_fhri: bool = True,
                                  fhri_threshold: float = 0.6,
                                  entropy_threshold: float = 2.0) -> Dict[str, float]:
    """
    Calculate precision, recall, F1 for a group of results.

    Args:
        results: List of evaluation results
        use_fhri: If True, use FHRI for detection; if False, use entropy only
        fhri_threshold: FHRI threshold for hallucination detection (lower = hallucination)
        entropy_threshold: Entropy threshold for hallucination detection (higher = hallucination)

    Returns:
        Dict with precision, recall, F1, accuracy
    """
    if not results:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "accuracy": 0.0, "count": 0}

    # Determine predictions based on detection method
    predictions = []
    true_labels = []

    for result in results:
        true_label = result.get("true_label", "accurate")
        true_labels.append(true_label)

        if use_fhri:
            # Use FHRI for detection
            fhri = result.get("fhri")
            if fhri is None:
                predicted = "accurate"  # Default if FHRI unavailable
            elif fhri < fhri_threshold:
                predicted = "hallucination"
            else:
                predicted = "accurate"
        else:
            # Use entropy only
            entropy = result.get("entropy")
            if entropy is None:
                predicted = "accurate"
            elif entropy > entropy_threshold:
                predicted = "hallucination"
            else:
                predicted = "accurate"

        predictions.append(predicted)

    # Calculate binary classification metrics (hallucination vs accurate)
    # We simplify to binary: hallucination=positive, accurate=negative
    tp = sum(1 for i in range(len(predictions))
             if true_labels[i] in ["hallucination", "contradiction"] and predictions[i] == "hallucination")
    fp = sum(1 for i in range(len(predictions))
             if true_labels[i] == "accurate" and predictions[i] == "hallucination")
    fn = sum(1 for i in range(len(predictions))
             if true_labels[i] in ["hallucination", "contradiction"] and predictions[i] == "accurate")
    tn = sum(1 for i in range(len(predictions))
             if true_labels[i] == "accurate" and predictions[i] == "accurate")

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(predictions) if len(predictions) > 0 else 0.0

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "accuracy": round(accuracy, 3),
        "count": len(results),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn
    }


def analyze_by_scenario(report: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze evaluation results grouped by scenario."""
    detailed_results = report.get("detailed_results", [])

    if not detailed_results:
        print("⚠ No detailed results found in report")
        return {}

    # Group by scenario
    scenario_groups = group_by_scenario(detailed_results)

    print(f"\n{'=' * 60}")
    print("SCENARIO-BASED FHRI EVALUATION")
    print(f"{'=' * 60}")
    print(f"Total samples: {len(detailed_results)}")
    print(f"Scenarios detected: {len(scenario_groups)}")
    print(f"{'=' * 60}\n")

    # Analyze each scenario
    scenario_analysis = {}

    # Scenario name mapping
    scenario_names = {
        "numeric_kpi": "Numeric KPI / Ratios",
        "directional": "Directional Recap",
        "intraday": "Intraday / Real-time",
        "fundamentals": "Fundamentals / Long Horizon",
        "regulatory": "Regulatory / Policy",
        "advice": "Portfolio Advice / Suitability",
        "multi_ticker": "Multi-Ticker Comparison",
        "news": "News Summarization",
        "default": "Default"
    }

    for scenario_id, results in scenario_groups.items():
        scenario_name = scenario_names.get(scenario_id, scenario_id)

        print(f"\n{scenario_name} ({scenario_id})")
        print("-" * 60)
        print(f"Samples: {len(results)}")

        # Calculate metrics for entropy-only
        entropy_metrics = calculate_metrics_for_group(results, use_fhri=False)

        # Calculate metrics for FHRI
        fhri_metrics = calculate_metrics_for_group(results, use_fhri=True)

        print(f"\nEntropy-only Detection:")
        print(f"  Precision: {entropy_metrics['precision']:.3f}")
        print(f"  Recall:    {entropy_metrics['recall']:.3f}")
        print(f"  F1-Score:  {entropy_metrics['f1']:.3f}")
        print(f"  Accuracy:  {entropy_metrics['accuracy']:.3f}")

        print(f"\nFHRI Detection:")
        print(f"  Precision: {fhri_metrics['precision']:.3f}")
        print(f"  Recall:    {fhri_metrics['recall']:.3f}")
        print(f"  F1-Score:  {fhri_metrics['f1']:.3f}")
        print(f"  Accuracy:  {fhri_metrics['accuracy']:.3f}")

        # Improvement
        f1_improvement = fhri_metrics['f1'] - entropy_metrics['f1']
        print(f"\nF1 Improvement: {f1_improvement:+.3f} ({f1_improvement/max(entropy_metrics['f1'], 0.001)*100:+.1f}%)")

        scenario_analysis[scenario_id] = {
            "scenario_name": scenario_name,
            "count": len(results),
            "entropy_only": entropy_metrics,
            "fhri": fhri_metrics,
            "f1_improvement": round(f1_improvement, 3),
            "f1_improvement_percent": round(f1_improvement/max(entropy_metrics['f1'], 0.001)*100, 1)
        }

    # Overall comparison
    print(f"\n{'=' * 60}")
    print("OVERALL COMPARISON")
    print(f"{'=' * 60}")

    overall_entropy = calculate_metrics_for_group(detailed_results, use_fhri=False)
    overall_fhri = calculate_metrics_for_group(detailed_results, use_fhri=True)

    print(f"\nEntropy-only (Overall):")
    print(f"  Precision: {overall_entropy['precision']:.3f}")
    print(f"  Recall:    {overall_entropy['recall']:.3f}")
    print(f"  F1-Score:  {overall_entropy['f1']:.3f}")
    print(f"  Accuracy:  {overall_entropy['accuracy']:.3f}")

    print(f"\nFHRI (Overall):")
    print(f"  Precision: {overall_fhri['precision']:.3f}")
    print(f"  Recall:    {overall_fhri['recall']:.3f}")
    print(f"  F1-Score:  {overall_fhri['f1']:.3f}")
    print(f"  Accuracy:  {overall_fhri['accuracy']:.3f}")

    overall_f1_improvement = overall_fhri['f1'] - overall_entropy['f1']
    print(f"\nOverall F1 Improvement: {overall_f1_improvement:+.3f} ({overall_f1_improvement/max(overall_entropy['f1'], 0.001)*100:+.1f}%)")

    return {
        "by_scenario": scenario_analysis,
        "overall": {
            "entropy_only": overall_entropy,
            "fhri": overall_fhri,
            "f1_improvement": round(overall_f1_improvement, 3),
            "f1_improvement_percent": round(overall_f1_improvement/max(overall_entropy['f1'], 0.001)*100, 1)
        },
        "scenario_counts": {scenario_names.get(k, k): v for k, v in
                            {k: len(v) for k, v in scenario_groups.items()}.items()}
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate FHRI detection by scenario")
    parser.add_argument("--report", type=str, required=True,
                       help="Path to evaluation report JSON (from evaluate_detection.py)")
    parser.add_argument("--output", type=str, default="results/scenario_analysis.json",
                       help="Output path for scenario analysis JSON")

    args = parser.parse_args()

    # Load report
    print(f"Loading evaluation report from: {args.report}")
    report = load_evaluation_report(args.report)

    # Analyze by scenario
    analysis = analyze_by_scenario(report)

    # Save analysis
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"Scenario analysis saved to: {output_path}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
