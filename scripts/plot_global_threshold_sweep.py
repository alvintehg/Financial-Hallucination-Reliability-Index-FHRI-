"""
Generate Figure 4.1: Global threshold sweep visualization.

This script creates a multi-line chart showing trade-off curves for:
- Overall Accuracy (blue)
- Hallucination Recall (red)
- Contradiction Recall (orange)
- Macro F1 (green)

Highlights the optimal point at threshold=0.70.

Usage:
    python scripts/plot_global_threshold_sweep.py --input results/threshold_sweep_static/sweep_static_summary.csv --output results/plots/figure_4_1_global_threshold_sweep.png
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def plot_global_threshold_sweep(csv_path: Path, output_path: Path, optimal_threshold: float = 0.70):
    """
    Create Figure 4.1: Multi-line chart showing trade-off curves.

    Args:
        csv_path: Path to sweep_static_summary.csv
        output_path: Path to save the figure
        optimal_threshold: The optimal threshold to highlight (default: 0.70)
    """
    # Read data
    df = pd.read_csv(csv_path)

    # Create figure
    plt.figure(figsize=(12, 7))

    # Plot the four metrics
    plt.plot(df["threshold"], df["accuracy"] * 100,
             marker='o', linewidth=2, markersize=8,
             color='#3498db', label='Overall Accuracy')

    plt.plot(df["threshold"], df["hall_recall"] * 100,
             marker='s', linewidth=2, markersize=8,
             color='#e74c3c', label='Hallucination Recall')

    plt.plot(df["threshold"], df["contr_recall"] * 100,
             marker='^', linewidth=2, markersize=8,
             color='#f39c12', label='Contradiction Recall')

    plt.plot(df["threshold"], df["macro_f1"] * 100,
             marker='D', linewidth=2, markersize=8,
             color='#2ecc71', label='Macro F1')

    # Highlight optimal threshold
    if optimal_threshold in df["threshold"].values:
        opt_row = df[df["threshold"] == optimal_threshold].iloc[0]

        # Add vertical line at optimal threshold
        plt.axvline(x=optimal_threshold, color='gray', linestyle='--',
                   linewidth=1.5, alpha=0.7, label=f'Optimal τ = {optimal_threshold:.2f}')

        # Add marker at optimal point for Macro F1
        plt.scatter(optimal_threshold, opt_row["macro_f1"] * 100,
                   s=200, color='#2ecc71', edgecolors='black',
                   linewidths=2, zorder=5, marker='*')

        # Add annotation
        plt.annotate(
            f'Optimal Point\n(τ={optimal_threshold:.2f}, F1={opt_row["macro_f1"]:.4f})',
            xy=(optimal_threshold, opt_row["macro_f1"] * 100),
            xytext=(optimal_threshold + 0.05, opt_row["macro_f1"] * 100 + 5),
            fontsize=10,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.3),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', lw=1.5)
        )

    # Formatting
    plt.xlabel('FHRI Threshold (τ)', fontsize=13, fontweight='bold')
    plt.ylabel('Performance Metric (%)', fontsize=13, fontweight='bold')
    plt.title('Figure 4.1: Global Threshold Sweep Visualization\nTrade-off between Accuracy and Hallucination Recall',
              fontsize=14, fontweight='bold', pad=20)

    # Grid
    plt.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

    # Legend
    plt.legend(loc='best', fontsize=11, framealpha=0.9, shadow=True)

    # Set axis limits
    plt.xlim(df["threshold"].min() - 0.02, df["threshold"].max() + 0.02)
    plt.ylim(0, 105)

    # Tight layout
    plt.tight_layout()

    # Save
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved Figure 4.1 to: {output_path}")

    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Generate Figure 4.1: Global threshold sweep visualization"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="results/threshold_sweep_static_global_full/sweep_static_summary.csv",
        help="Path to sweep_static_summary.csv"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/plots/figure_4_1_global_threshold_sweep.png",
        help="Output path for the figure"
    )
    parser.add_argument(
        "--optimal_threshold",
        type=float,
        default=0.70,
        help="Optimal threshold to highlight (default: 0.70)"
    )

    args = parser.parse_args()

    csv_path = Path(args.input)
    output_path = Path(args.output)

    # Validate input
    if not csv_path.exists():
        print(f"[ERROR] Input file not found: {csv_path}")
        print("\nPlease run the threshold sweep first:")
        print("  python scripts/run_threshold_sweep.py")
        sys.exit(1)

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate plot
    plot_global_threshold_sweep(csv_path, output_path, args.optimal_threshold)

    print("\n" + "=" * 60)
    print("Figure 4.1 Generation Complete")
    print("=" * 60)
    print(f"\nVisualization saved to: {output_path}")
    print("\nThis figure shows the trade-off between:")
    print("  - Higher threshold -> Higher accuracy, Lower hallucination recall")
    print("  - Lower threshold -> Lower accuracy, Higher hallucination recall")
    print(f"  - Optimal balance at threshold = {args.optimal_threshold:.2f}")


if __name__ == "__main__":
    main()
