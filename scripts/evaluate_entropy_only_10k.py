"""
Quick Entropy-Only Evaluation on 10k Static Dataset

This script evaluates ONLY the entropy component (E) to establish a baseline
for comparison with full FHRI and scenario-specific approaches.
"""

import json
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def calculate_entropy_only_metrics(dataset_path: str):
    """
    Evaluate entropy-only detection on static dataset.

    Simple rule: If entropy > 2.0, flag as hallucination
    """
    with open(dataset_path) as f:
        data = json.load(f)

    # Handle nested structure
    if isinstance(data, dict) and "samples" in data:
        samples = data["samples"]
        # Flatten if nested list
        if samples and isinstance(samples[0], list):
            samples = [item for sublist in samples for item in sublist]
    elif isinstance(data, list):
        samples = data
    else:
        samples = []

    results = {
        "accurate": {"tp": 0, "fp": 0, "fn": 0},
        "hallucination": {"tp": 0, "fp": 0, "fn": 0},
        "contradiction": {"tp": 0, "fp": 0, "fn": 0}
    }

    total = 0
    correct = 0

    for sample in samples:
        true_label = sample.get("ground_truth_label", "").lower()

        # Skip if no label
        if not true_label or true_label not in ["accurate", "hallucination", "contradiction"]:
            continue

        # For entropy-only, we only detect hallucinations
        # Since we don't have actual entropy values in the dataset,
        # we need to estimate based on the answer
        # This is a placeholder - in reality you'd compute actual entropy

        # Simplified logic: assume all samples are predicted as "accurate"
        # since entropy-only has no way to detect without running the model
        predicted_label = "accurate"

        total += 1

        if predicted_label == true_label:
            correct += 1
            results[true_label]["tp"] += 1
        else:
            results[true_label]["fn"] += 1
            results[predicted_label]["fp"] += 1

    # Calculate metrics
    accuracy = correct / total if total > 0 else 0

    metrics = {}
    for label in ["accurate", "hallucination", "contradiction"]:
        tp = results[label]["tp"]
        fp = results[label]["fp"]
        fn = results[label]["fn"]

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        metrics[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "support": tp + fn
        }

    macro_f1 = sum(m["f1"] for m in metrics.values()) / 3

    return {
        "overall": {
            "accuracy": accuracy,
            "macro_f1": macro_f1,
            "total_samples": total,
            "correct_predictions": correct
        },
        "per_class": metrics
    }

if __name__ == "__main__":
    dataset_path = PROJECT_ROOT / "data" / "fhri_evaluation_dataset_full.json"

    print("=" * 60)
    print("ENTROPY-ONLY BASELINE EVALUATION")
    print("=" * 60)
    print(f"\nDataset: {dataset_path}")
    print("\nNOTE: This is a PLACEHOLDER evaluation.")
    print("Entropy-only method requires actual entropy computation from LLM.")
    print("For accurate results, you need to:")
    print("  1. Run the model on all samples")
    print("  2. Compute MC-Dropout entropy for each response")
    print("  3. Apply threshold (e.g., entropy > 2.0 = hallucination)")
    print("\n" + "=" * 60)

    results = calculate_entropy_only_metrics(str(dataset_path))

    print("\nOVERALL METRICS:")
    print(f"  Accuracy: {results['overall']['accuracy']:.2%}")
    print(f"  Macro F1: {results['overall']['macro_f1']:.4f}")
    print(f"  Total Samples: {results['overall']['total_samples']}")

    print("\nPER-CLASS METRICS:")
    for label, metrics in results['per_class'].items():
        print(f"\n{label.upper()}:")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall: {metrics['recall']:.4f}")
        print(f"  F1: {metrics['f1']:.4f}")
        print(f"  Support: {metrics['support']}")

    # Save results
    output_path = PROJECT_ROOT / "results" / "eval_entropy_only_placeholder.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_path}")
