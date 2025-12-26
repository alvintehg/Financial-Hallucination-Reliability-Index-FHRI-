"""
Compare evaluation results for different thresholds.

Usage:
    python scripts/compare_thresholds.py \
        --result1 results/test_0.65_fixed.json \
        --result2 results/test_0.70_fixed.json
"""

import json
import argparse
import sys
from pathlib import Path


def load_results(filepath: str):
    """Load evaluation results from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def compare_results(result1: dict, result2: dict, name1: str = "Result 1", name2: str = "Result 2"):
    """Compare two evaluation results side-by-side."""
    
    metrics1 = result1.get("metrics", {})
    metrics2 = result2.get("metrics", {})
    
    print("=" * 80)
    print("THRESHOLD COMPARISON")
    print("=" * 80)
    print(f"\n{name1:40} | {name2:40}")
    print("-" * 80)
    
    # Overall metrics
    overall1 = metrics1.get("overall", {})
    overall2 = metrics2.get("overall", {})
    
    print("\n[OVERALL METRICS]")
    print(f"{'Accuracy:':30} {overall1.get('accuracy', 0):.4f} | {overall2.get('accuracy', 0):.4f}")
    print(f"{'Macro F1:':30} {overall1.get('macro_f1', 0):.4f} | {overall2.get('macro_f1', 0):.4f}")
    print(f"{'Correct Predictions:':30} {overall1.get('correct_predictions', 0)}/100 | {overall2.get('correct_predictions', 0)}/100")
    
    # Per-class metrics
    classes = ["accurate", "hallucination", "contradiction"]
    
    print("\n[PER-CLASS F1 SCORES]")
    for class_name in classes:
        class1 = metrics1.get(class_name, {})
        class2 = metrics2.get(class_name, {})
        f1_1 = class1.get("f1_score", 0)
        f1_2 = class2.get("f1_score", 0)
        
        # Determine winner
        if f1_1 > f1_2:
            winner = f"{name1} (+{f1_1 - f1_2:.4f})"
        elif f1_2 > f1_1:
            winner = f"{name2} (+{f1_2 - f1_1:.4f})"
        else:
            winner = "Tie"
        
        print(f"{class_name.capitalize() + ' F1:':30} {f1_1:.4f} | {f1_2:.4f} ({winner})")
    
    # Precision and Recall
    print("\n[PRECISION & RECALL]")
    for class_name in classes:
        class1 = metrics1.get(class_name, {})
        class2 = metrics2.get(class_name, {})
        prec1 = class1.get("precision", 0)
        prec2 = class2.get("precision", 0)
        rec1 = class1.get("recall", 0)
        rec2 = class2.get("recall", 0)
        
        print(f"\n{class_name.capitalize()}:")
        print(f"  Precision: {prec1:.4f} | {prec2:.4f}")
        print(f"  Recall:    {rec1:.4f} | {rec2:.4f}")
    
    # Confusion matrix summary
    print("\n[FALSE POSITIVES & NEGATIVES]")
    for class_name in classes:
        class1 = metrics1.get(class_name, {})
        class2 = metrics2.get(class_name, {})
        fp1 = class1.get("false_positives", 0)
        fp2 = class2.get("false_positives", 0)
        fn1 = class1.get("false_negatives", 0)
        fn2 = class2.get("false_negatives", 0)
        
        print(f"\n{class_name.capitalize()}:")
        print(f"  False Positives:  {fp1} | {fp2}")
        print(f"  False Negatives:  {fn1} | {fn2}")
    
    # Summary recommendation
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    
    macro_f1_1 = overall1.get("macro_f1", 0)
    macro_f1_2 = overall2.get("macro_f1", 0)
    acc1 = overall1.get("accuracy", 0)
    acc2 = overall2.get("accuracy", 0)
    
    if macro_f1_1 > macro_f1_2:
        print(f"\n{name1} is BETTER:")
        print(f"  - Higher Macro F1: {macro_f1_1:.4f} vs {macro_f1_2:.4f} (+{macro_f1_1 - macro_f1_2:.4f})")
        if acc1 > acc2:
            print(f"  - Higher Accuracy: {acc1:.4f} vs {acc2:.4f} (+{acc1 - acc2:.4f})")
    elif macro_f1_2 > macro_f1_1:
        print(f"\n{name2} is BETTER:")
        print(f"  - Higher Macro F1: {macro_f1_2:.4f} vs {macro_f1_1:.4f} (+{macro_f1_2 - macro_f1_1:.4f})")
        if acc2 > acc1:
            print(f"  - Higher Accuracy: {acc2:.4f} vs {acc1:.4f} (+{acc2 - acc1:.4f})")
    else:
        print("\nBoth thresholds perform similarly.")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare evaluation results")
    parser.add_argument(
        "--result1",
        type=str,
        required=True,
        help="Path to first evaluation results JSON"
    )
    parser.add_argument(
        "--result2",
        type=str,
        required=True,
        help="Path to second evaluation results JSON"
    )
    parser.add_argument(
        "--name1",
        type=str,
        default="Result 1",
        help="Name for first result"
    )
    parser.add_argument(
        "--name2",
        type=str,
        default="Result 2",
        help="Name for second result"
    )
    
    args = parser.parse_args()
    
    # Load results
    result1 = load_results(args.result1)
    result2 = load_results(args.result2)
    
    # Compare
    compare_results(result1, result2, args.name1, args.name2)














