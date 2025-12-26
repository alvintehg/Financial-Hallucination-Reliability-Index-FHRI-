"""
Script to find the optimal FHRI threshold based on evaluation results.

Usage:
    python scripts/find_optimal_threshold.py --evaluation results/eval_fhri.json
"""

import json
import argparse
import numpy as np
from typing import Dict, List, Any


def calculate_metrics_at_threshold(results: List[Dict], threshold: float) -> Dict[str, float]:
    """Calculate precision, recall, F1 at a given FHRI threshold."""
    # Filter out samples without FHRI scores
    valid_results = [r for r in results if r.get("fhri") is not None]
    
    if not valid_results:
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}
    
    # Predict: FHRI >= threshold = accurate, FHRI < threshold = hallucination
    # (We'll treat contradiction as a separate case for now)
    tp = 0  # True positive: predicted accurate, actually accurate
    fp = 0  # False positive: predicted accurate, actually hallucination
    fn = 0  # False negative: predicted hallucination, actually accurate
    tn = 0  # True negative: predicted hallucination, actually hallucination
    
    for r in valid_results:
        true_label = r["true_label"]
        fhri = r["fhri"]
        
        # Skip contradiction samples for binary threshold finding
        if true_label == "contradiction":
            continue
        
        predicted = "accurate" if fhri >= threshold else "hallucination"
        
        if predicted == "accurate" and true_label == "accurate":
            tp += 1
        elif predicted == "accurate" and true_label == "hallucination":
            fp += 1
        elif predicted == "hallucination" and true_label == "accurate":
            fn += 1
        elif predicted == "hallucination" and true_label == "hallucination":
            tn += 1
    
    total = tp + fp + fn + tn
    if total == 0:
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}
    
    accuracy = (tp + tn) / total
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "total": total
    }


def find_optimal_threshold(evaluation_path: str) -> None:
    """Find optimal FHRI threshold by testing multiple values."""
    print("=" * 60)
    print("FINDING OPTIMAL FHRI THRESHOLD")
    print("=" * 60)
    
    # Load evaluation results
    with open(evaluation_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    results = report.get("detailed_results", [])
    print(f"\nLoaded {len(results)} evaluation results")
    
    # Filter to samples with FHRI scores
    valid_results = [r for r in results if r.get("fhri") is not None]
    print(f"Found {len(valid_results)} samples with FHRI scores")
    
    if not valid_results:
        print("✗ No FHRI scores found in evaluation results!")
        return
    
    # Test thresholds from 0.3 to 0.9 in 0.05 steps
    thresholds = np.arange(0.30, 0.95, 0.05)
    best_threshold = None
    best_f1 = 0.0
    best_metrics = None
    
    print(f"\n{'Threshold':<12} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1-Score':<12}")
    print("-" * 60)
    
    results_by_threshold = []
    
    for threshold in thresholds:
        metrics = calculate_metrics_at_threshold(valid_results, threshold)
        results_by_threshold.append({
            "threshold": round(threshold, 2),
            **metrics
        })
        
        print(f"{threshold:<12.2f} {metrics['accuracy']:<12.4f} {metrics['precision']:<12.4f} {metrics['recall']:<12.4f} {metrics['f1']:<12.4f}")
        
        if metrics['f1'] > best_f1:
            best_f1 = metrics['f1']
            best_threshold = threshold
            best_metrics = metrics
    
    print("\n" + "=" * 60)
    print("OPTIMAL THRESHOLD FOUND")
    print("=" * 60)
    print(f"\nBest Threshold: {best_threshold:.2f}")
    print(f"Best F1-Score: {best_f1:.4f}")
    print(f"\nMetrics at optimal threshold:")
    print(f"  Accuracy:  {best_metrics['accuracy']:.4f}")
    print(f"  Precision: {best_metrics['precision']:.4f}")
    print(f"  Recall:    {best_metrics['recall']:.4f}")
    print(f"  F1-Score:  {best_metrics['f1']:.4f}")
    print(f"\nConfusion Matrix:")
    print(f"  True Positives:  {best_metrics['tp']}")
    print(f"  False Positives: {best_metrics['fp']}")
    print(f"  False Negatives: {best_metrics['fn']}")
    print(f"  True Negatives:  {best_metrics['tn']}")
    
    # Save results
    output_path = evaluation_path.replace('.json', '_threshold_analysis.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "optimal_threshold": round(best_threshold, 2),
            "optimal_metrics": {k: round(v, 4) if isinstance(v, float) else v 
                              for k, v in best_metrics.items()},
            "all_thresholds": results_by_threshold
        }, f, indent=2)
    
    print(f"\n✓ Detailed analysis saved to: {output_path}")
    print(f"\n💡 Recommendation: Use FHRI threshold = {best_threshold:.2f} for your evaluation")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find optimal FHRI threshold")
    parser.add_argument(
        "--evaluation",
        type=str,
        default="results/eval_fhri.json",
        help="Path to FHRI evaluation results JSON"
    )
    
    args = parser.parse_args()
    find_optimal_threshold(args.evaluation)






























