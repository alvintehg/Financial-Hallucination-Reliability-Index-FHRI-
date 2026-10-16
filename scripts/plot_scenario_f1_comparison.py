"""
Generate Figure 4.3: Per-scenario F1-score comparison (grouped bar chart).

This script creates a grouped bar chart showing F1-scores for each financial scenario:
- Overall F1
- Hallucination F1
- Contradiction F1

Scenarios are sorted by overall F1 descending.

Usage:
    python scripts/plot_scenario_f1_comparison.py --base results/threshold_sweep_per_scenario_full --output results/plots/figure_4_3_scenario_f1_comparison.png
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def load_scenario_data(base_dir: Path):
    """
    Load F1-score data from all scenario subdirectories.

    Returns:
        DataFrame with columns: scenario, overall_f1, hall_f1, contr_f1, optimal_threshold
    """
    scenario_data = []

    for scenario_dir in sorted(base_dir.iterdir()):
        if not scenario_dir.is_dir():
            continue

        scenario_name = scenario_dir.name

        # Skip portfolio_advice
        if scenario_name == 'portfolio_advice':
            print(f"[INFO] Skipping portfolio_advice as requested")
            continue

        csv_path = scenario_dir / "sweep_static_summary.csv"

        if not csv_path.exists():
            print(f"[WARN] Missing CSV for {scenario_name}, skipping")
            continue

        # Read the CSV
        df = pd.read_csv(csv_path)

        # Find the row with maximum macro_f1
        if 'macro_f1' in df.columns:
            best_idx = df['macro_f1'].idxmax()
            best_row = df.iloc[best_idx]

            scenario_data.append({
                'scenario': scenario_name,
                'optimal_threshold': best_row['threshold'],
                'overall_f1': best_row['macro_f1'],
                'hall_f1': best_row.get('hall_f1', 0),
                'contr_f1': best_row.get('contr_f1', 0),
                'accurate_f1': best_row.get('accurate_f1', 0),
                'accuracy': best_row.get('accuracy', 0)
            })

    return pd.DataFrame(scenario_data)


def plot_scenario_f1_comparison(base_dir: Path, output_path: Path):
    """
    Create Figure 4.3: Grouped bar chart of per-scenario F1-scores.

    Args:
        base_dir: Directory containing per-scenario sweep results
        output_path: Path to save the figure
    """
    # Load data
    df = load_scenario_data(base_dir)

    if df.empty:
        print("[ERROR] No scenario data found!")
        sys.exit(1)

    # Sort by overall F1 descending
    df = df.sort_values('overall_f1', ascending=False)

    # Prepare data for plotting
    scenarios = df['scenario'].tolist()
    overall_f1 = df['overall_f1'].tolist()
    hall_f1 = df['hall_f1'].tolist()
    accurate_f1 = df['accurate_f1'].tolist()
    contr_f1 = df['contr_f1'].tolist()

    # Create figure
    fig, ax = plt.subplots(figsize=(16, 8))

    # Bar positions
    x = np.arange(len(scenarios))
    width = 0.20

    # Create bars - 4 bars per scenario
    bars1 = ax.bar(x - 1.5*width, overall_f1, width, label='Macro F1',
                   color='#3498db', alpha=0.8, edgecolor='black', linewidth=0.5)
    bars2 = ax.bar(x - 0.5*width, hall_f1, width, label='Hallucination F1',
                   color='#e74c3c', alpha=0.8, edgecolor='black', linewidth=0.5)
    bars3 = ax.bar(x + 0.5*width, accurate_f1, width, label='Accurate F1',
                   color='#f39c12', alpha=0.8, edgecolor='black', linewidth=0.5)
    bars4 = ax.bar(x + 1.5*width, contr_f1, width, label='Contradiction F1',
                   color='#2ecc71', alpha=0.8, edgecolor='black', linewidth=0.5)

    # Add value labels on bars
    def add_labels(bars):
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.3f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom',
                       fontsize=8, fontweight='bold')

    add_labels(bars1)
    add_labels(bars2)
    add_labels(bars3)
    add_labels(bars4)

    # Labels and title
    ax.set_xlabel('Financial Scenario', fontsize=13, fontweight='bold')
    ax.set_ylabel('F1-Score', fontsize=13, fontweight='bold')
    ax.set_title('Figure 4.3: Per-Scenario F1-Score Comparison\n(Macro F1, Hallucination F1, Accurate F1, Contradiction F1 - Sorted by Macro F1 Descending)',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, rotation=45, ha='right')
    ax.legend(loc='upper right', fontsize=11, framealpha=0.9, shadow=True)
    ax.set_ylim([0, 1.1])
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)

    # Tight layout
    plt.tight_layout()

    # Save
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved Figure 4.3 to: {output_path}")

    # Print summary
    print("\n" + "=" * 80)
    print("Per-Scenario F1-Score Summary")
    print("=" * 80)
    print(f"{'Scenario':<20} {'Optimal T':>10} {'Overall F1':>12} {'Hall F1':>10} {'Contr F1':>10} {'Accuracy':>10}")
    print("-" * 80)

    for _, row in df.iterrows():
        print(f"{row['scenario']:<20} {row['optimal_threshold']:>10.2f} "
              f"{row['overall_f1']:>12.4f} {row['hall_f1']:>10.4f} "
              f"{row['contr_f1']:>10.4f} {row['accuracy']:>10.2%}")

    print("\n" + "=" * 80)
    print(f"Best performing scenario: {df.iloc[0]['scenario']} (F1={df.iloc[0]['overall_f1']:.4f})")
    print(f"Worst performing scenario: {df.iloc[-1]['scenario']} (F1={df.iloc[-1]['overall_f1']:.4f})")
    print(f"Average F1 across scenarios: {df['overall_f1'].mean():.4f}")
    print("=" * 80)

    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Generate Figure 4.3: Per-scenario F1-score comparison"
    )
    parser.add_argument(
        "--base",
        type=str,
        default="results/threshold_sweep_per_scenario_full",
        help="Base directory containing per-scenario sweep outputs"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/plots/figure_4_3_scenario_f1_comparison.png",
        help="Output path for the figure"
    )

    args = parser.parse_args()

    base_dir = Path(args.base)
    output_path = Path(args.output)

    # Validate input
    if not base_dir.exists():
        print(f"[ERROR] Base directory not found: {base_dir}")
        print("\nPlease run scenario sweeps first:")
        print("  python scripts/run_scenario_sweeps.py")
        sys.exit(1)

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate plot
    plot_scenario_f1_comparison(base_dir, output_path)

    print("\n" + "=" * 60)
    print("Figure 4.3 Generation Complete")
    print("=" * 60)
    print(f"\nVisualization saved to: {output_path}")


if __name__ == "__main__":
    main()
