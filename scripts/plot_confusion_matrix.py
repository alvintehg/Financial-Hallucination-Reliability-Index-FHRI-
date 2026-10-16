"""
Generate Figure 4.2: Confusion matrix for global threshold=0.70.

This script creates a 3x3 heatmap showing the number of correct/incorrect
classifications for each class: Accurate, Hallucination, and Contradiction.

Usage:
    python scripts/plot_confusion_matrix.py --input results/threshold_sweep_static_global_full/sweep_static_fhri_0_70.json --output results/plots/figure_4_2_confusion_matrix.png
"""

import argparse
import sys
import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def plot_confusion_matrix(json_path: Path, output_path: Path, threshold: float = 0.70):
    """
    Create Figure 4.2: 3x3 confusion matrix heatmap.

    Args:
        json_path: Path to the evaluation JSON report
        output_path: Path to save the figure
        threshold: The threshold value used (for title)
    """
    # Read evaluation results
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extract confusion matrix
    confusion_matrix = data.get('confusion_matrix', {})

    # Define class order
    classes = ['accurate', 'hallucination', 'contradiction']
    class_labels = ['Accurate', 'Hallucination', 'Contradiction']

    # Build confusion matrix as numpy array
    n_classes = len(classes)
    matrix = np.zeros((n_classes, n_classes), dtype=int)

    for i, true_class in enumerate(classes):
        for j, pred_class in enumerate(classes):
            matrix[i, j] = confusion_matrix.get(true_class, {}).get(pred_class, 0)

    # Create figure
    plt.figure(figsize=(10, 8))

    # Create heatmap with annotations
    ax = sns.heatmap(
        matrix,
        annot=True,
        fmt='d',
        cmap='Blues',
        xticklabels=class_labels,
        yticklabels=class_labels,
        cbar_kws={'label': 'Count'},
        linewidths=1,
        linecolor='gray',
        square=True,
        annot_kws={'fontsize': 14, 'fontweight': 'bold'}
    )

    # Labels and title
    plt.xlabel('Predicted Label', fontsize=13, fontweight='bold')
    plt.ylabel('True Label', fontsize=13, fontweight='bold')
    plt.title(f'Figure 4.2: Confusion Matrix for Global Threshold = {threshold:.2f}\n' +
              '(3x3 heatmap showing correct/incorrect classifications)',
              fontsize=14, fontweight='bold', pad=20)

    # Rotate labels for better readability
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)

    # Tight layout
    plt.tight_layout()

    # Save
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved Figure 4.2 to: {output_path}")

    # Print summary statistics
    print("\n" + "=" * 60)
    print("Confusion Matrix Summary")
    print("=" * 60)

    for i, true_label in enumerate(class_labels):
        correct = matrix[i, i]
        total = matrix[i, :].sum()
        accuracy = (correct / total * 100) if total > 0 else 0
        print(f"{true_label:15s}: {correct:4d}/{total:4d} correct ({accuracy:5.1f}%)")

    print("\nKey Observations:")
    # Check for perfect diagonal elements
    for i, label in enumerate(class_labels):
        if i < len(matrix) and matrix[i, i] == matrix[i, :].sum():
            print(f"  - {label}: Perfect classification (100%)")

    # Check for major misclassifications
    for i, true_label in enumerate(class_labels):
        for j, pred_label in enumerate(class_labels):
            if i != j and matrix[i, j] > 0:
                pct = matrix[i, j] / matrix[i, :].sum() * 100
                if pct > 10:  # Report if > 10% misclassification
                    print(f"  - {matrix[i, j]} {true_label} misclassified as {pred_label} ({pct:.1f}%)")

    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Generate Figure 4.2: Confusion matrix visualization"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="results/threshold_sweep_static_global_full/sweep_static_fhri_0_70.json",
        help="Path to evaluation JSON report (threshold 0.70)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/plots/figure_4_2_confusion_matrix.png",
        help="Output path for the figure"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.70,
        help="Threshold value for the title (default: 0.70)"
    )

    args = parser.parse_args()

    json_path = Path(args.input)
    output_path = Path(args.output)

    # Validate input
    if not json_path.exists():
        print(f"[ERROR] Input file not found: {json_path}")
        print("\nPlease run the threshold sweep first:")
        print("  python scripts/run_threshold_sweep.py")
        sys.exit(1)

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate plot
    plot_confusion_matrix(json_path, output_path, args.threshold)

    print("\n" + "=" * 60)
    print("Figure 4.2 Generation Complete")
    print("=" * 60)
    print(f"\nVisualization saved to: {output_path}")


if __name__ == "__main__":
    main()
