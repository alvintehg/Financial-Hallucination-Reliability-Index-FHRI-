"""
Generate missing plots for Results Chapter (Chapter 4).

This script creates the following visualizations:
1. Figure 4.3: Threshold adjustment heatmap by scenario
2. Figure 4.4: Multi-scenario PR curve overlay (representative scenarios)
3. Figure 4.5: F1-score comparison bar chart across all scenarios
4. Figure 4.6: Error distribution pie chart (breakdown of missed hallucinations)
5. Table 4.6: FN hallucination breakdown by scenario

Usage:
    python scripts/plot_missing_results.py --baseline results/eval_10k_baseline_static.json --output results/plots/results_chapter
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd


def load_json(file_path: Path) -> Dict[str, Any]:
    """Load JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def plot_threshold_heatmap(output_dir: Path):
    """
    Figure 4.3: Heatmap showing threshold adjustments by scenario.

    Shows initial threshold → optimal threshold changes.
    """
    # Data from Table 4.4 (optimal threshold evaluation)
    data = {
        'numeric_kpi': {'initial': 0.75, 'optimal': 0.70, 'macro_f1': 0.8242, 'hall_recall': 0.80},
        'intraday': {'initial': 0.75, 'optimal': 0.65, 'macro_f1': 0.8242, 'hall_recall': 0.80},
        'directional': {'initial': 0.70, 'optimal': 0.65, 'macro_f1': 0.8242, 'hall_recall': 0.80},
        'regulatory': {'initial': 0.70, 'optimal': 0.55, 'macro_f1': 0.8242, 'hall_recall': 0.80},
        'fundamentals': {'initial': 0.75, 'optimal': 0.70, 'macro_f1': 0.8468, 'hall_recall': 0.90},
        'multi_ticker': {'initial': 0.65, 'optimal': 0.55, 'macro_f1': 0.8242, 'hall_recall': 0.80},
        'news': {'initial': 0.65, 'optimal': 0.60, 'macro_f1': 1.0000, 'hall_recall': 1.00},
        'crypto': {'initial': 0.65, 'optimal': 0.60, 'macro_f1': 1.0000, 'hall_recall': 1.00},
        'advice': {'initial': 0.50, 'optimal': 0.60, 'macro_f1': 1.0000, 'hall_recall': 1.00},
        'portfolio_advice': {'initial': 0.50, 'optimal': 0.50, 'macro_f1': 0.9555, 'hall_recall': 1.00},
        'default': {'initial': 0.70, 'optimal': 0.70, 'macro_f1': 0.8683, 'hall_recall': 1.00},
    }

    scenarios = list(data.keys())
    metrics = ['Initial τ', 'Optimal τ', 'Δ τ', 'Macro F1', 'Hall Recall']

    # Create matrix
    matrix = np.zeros((len(scenarios), len(metrics)))
    for i, scenario in enumerate(scenarios):
        matrix[i, 0] = data[scenario]['initial']
        matrix[i, 1] = data[scenario]['optimal']
        matrix[i, 2] = data[scenario]['optimal'] - data[scenario]['initial']
        matrix[i, 3] = data[scenario]['macro_f1']
        matrix[i, 4] = data[scenario]['hall_recall']

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Left panel: Threshold values
    threshold_matrix = matrix[:, :3]
    sns.heatmap(threshold_matrix, annot=True, fmt='.2f', cmap='RdYlGn_r',
                xticklabels=['Initial τ', 'Optimal τ', 'Δ τ'],
                yticklabels=[s.replace('_', ' ').title() for s in scenarios],
                ax=ax1, cbar_kws={'label': 'Threshold Value'}, vmin=-0.15, vmax=0.75,
                linewidths=0.5, linecolor='gray')
    ax1.set_title('Threshold Optimization by Scenario', fontsize=14, fontweight='bold', pad=15)
    ax1.set_xlabel('Threshold Metric', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Financial Scenario', fontsize=12, fontweight='bold')

    # Right panel: Performance metrics
    performance_matrix = matrix[:, 3:]
    sns.heatmap(performance_matrix, annot=True, fmt='.3f', cmap='YlGnBu',
                xticklabels=['Macro F1', 'Hall Recall'],
                yticklabels=[s.replace('_', ' ').title() for s in scenarios],
                ax=ax2, cbar_kws={'label': 'Score'}, vmin=0.80, vmax=1.0,
                linewidths=0.5, linecolor='gray')
    ax2.set_title('Performance at Optimal Threshold', fontsize=14, fontweight='bold', pad=15)
    ax2.set_xlabel('Performance Metric', fontsize=12, fontweight='bold')
    ax2.set_ylabel('')

    plt.tight_layout()
    out_path = output_dir / "figure_4_3_threshold_heatmap.png"
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved: {out_path}")
    plt.close()


def plot_multi_scenario_pr_curves(output_dir: Path):
    """
    Figure 4.4: Precision-Recall curves for representative scenarios.

    Overlay PR curves for Numeric KPI, Advice, and News scenarios.
    """
    # Check if per-scenario sweep data exists
    base_dir = Path("results/threshold_sweep_per_scenario")

    scenarios_to_plot = {
        'numeric_kpi': {'color': '#e74c3c', 'marker': 'o', 'label': 'Numeric KPI'},
        'advice': {'color': '#2ecc71', 'marker': 's', 'label': 'Advice'},
        'news': {'color': '#3498db', 'marker': '^', 'label': 'News'},
        'fundamentals': {'color': '#9b59b6', 'marker': 'd', 'label': 'Fundamentals (Best)'},
        'regulatory': {'color': '#f39c12', 'marker': 'v', 'label': 'Regulatory (Complex)'}
    }

    fig, ax = plt.subplots(figsize=(10, 8))

    for scenario, style in scenarios_to_plot.items():
        csv_path = base_dir / scenario / "sweep_static_summary.csv"

        if csv_path.exists():
            df = pd.read_csv(csv_path)
            ax.plot(df['hall_recall'], df['hall_precision'],
                   color=style['color'], marker=style['marker'],
                   linewidth=2.5, markersize=8, alpha=0.8,
                   label=style['label'])

            # Annotate optimal point (typically mid-range threshold)
            mid_idx = len(df) // 2
            ax.annotate(f"τ={df.iloc[mid_idx]['threshold']:.2f}",
                       xy=(df.iloc[mid_idx]['hall_recall'], df.iloc[mid_idx]['hall_precision']),
                       xytext=(10, 10), textcoords='offset points',
                       fontsize=8, alpha=0.7,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor=style['color'], alpha=0.3))
        else:
            print(f"[WARN] Missing sweep data for {scenario}, skipping")

    # Add reference lines
    ax.axhline(y=0.80, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='80% Precision Target')
    ax.axvline(x=0.80, color='gray', linestyle=':', linewidth=1, alpha=0.5, label='80% Recall Target')

    ax.set_xlabel('Recall (Hallucination Detection)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Precision (Hallucination Detection)', fontsize=13, fontweight='bold')
    ax.set_title('Precision-Recall Trade-off Across Financial Scenarios',
                fontsize=15, fontweight='bold', pad=15)
    ax.legend(loc='lower left', fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)

    # Add diagonal F1 iso-lines
    for f1 in [0.6, 0.7, 0.8, 0.9]:
        recall = np.linspace(0.01, 1.0, 100)
        precision = (f1 * recall) / (2 * recall - f1)
        precision = np.clip(precision, 0, 1)
        ax.plot(recall, precision, 'k--', alpha=0.15, linewidth=0.8)
        ax.text(0.95, (f1 * 0.95) / (2 * 0.95 - f1), f'F1={f1:.1f}',
               fontsize=8, alpha=0.4, ha='right')

    plt.tight_layout()
    out_path = output_dir / "figure_4_4_multi_scenario_pr_curves.png"
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved: {out_path}")
    plt.close()


def plot_scenario_f1_comparison(output_dir: Path):
    """
    Figure 4.5: Bar chart comparing F1 scores across all scenarios.

    Shows Macro-F1 for each scenario at optimal threshold.
    """
    # Data from optimal evaluation
    data = {
        'Numeric KPI': 0.8242,
        'Intraday': 0.8242,
        'Directional': 0.8242,
        'Regulatory': 0.8242,
        'Fundamentals': 0.8468,
        'Multi-Ticker': 0.8242,
        'News': 1.0000,
        'Crypto': 1.0000,
        'Advice': 1.0000,
        'Portfolio Advice': 0.9555,
        'Default': 0.8683
    }

    scenarios = list(data.keys())
    f1_scores = list(data.values())

    # Color code by performance tier
    colors = []
    for score in f1_scores:
        if score >= 0.95:
            colors.append('#27ae60')  # Green - Excellent
        elif score >= 0.85:
            colors.append('#f39c12')  # Orange - Good
        else:
            colors.append('#e74c3c')  # Red - Moderate

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(scenarios, f1_scores, color=colors, alpha=0.8, edgecolor='black', linewidth=1.2)

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.4f}',
                   xy=(bar.get_x() + bar.get_width() / 2, height),
                   xytext=(0, 5),
                   textcoords="offset points",
                   ha='center', va='bottom',
                   fontsize=10, fontweight='bold')

    # Add reference line at 0.80 (target performance)
    ax.axhline(y=0.80, color='gray', linestyle='--', linewidth=2, alpha=0.6, label='Baseline Target (0.80)')

    ax.set_ylabel('Macro F1-Score', fontsize=13, fontweight='bold')
    ax.set_xlabel('Financial Scenario', fontsize=13, fontweight='bold')
    ax.set_title('FHRI Detection Performance Across Financial Scenarios (Optimal Thresholds)',
                fontsize=14, fontweight='bold', pad=15)
    ax.set_ylim(0.75, 1.05)
    ax.set_xticklabels(scenarios, rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    # Add legend for color coding
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#27ae60', alpha=0.8, label='Excellent (F1 ≥ 0.95)'),
        Patch(facecolor='#f39c12', alpha=0.8, label='Good (0.85 ≤ F1 < 0.95)'),
        Patch(facecolor='#e74c3c', alpha=0.8, label='Moderate (F1 < 0.85)')
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=10, framealpha=0.9)

    plt.tight_layout()
    out_path = output_dir / "figure_4_5_scenario_f1_comparison.png"
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved: {out_path}")
    plt.close()


def analyze_false_negatives(baseline_data: Dict[str, Any], output_dir: Path):
    """
    Figure 4.6: Error distribution pie chart.
    Table 4.6: Breakdown of 400 missed hallucinations by scenario and error type.

    Categorizes the 400 false negative hallucinations by:
    1. Scenario
    2. Error type (Numeric, Temporal, Grounding, Citation)
    """
    detailed_results = baseline_data.get('detailed_results', [])

    # Extract false negatives (true=hallucination, predicted=accurate or contradiction)
    false_negatives = []
    for result in detailed_results:
        true_label = result.get('true_label', '')
        pred_label = result.get('predicted_label', '')

        if true_label == 'hallucination' and pred_label != 'hallucination':
            false_negatives.append(result)

    total_fn = len(false_negatives)
    print(f"[INFO] Total false negatives found: {total_fn}")

    if total_fn == 0:
        print("[WARN] No false negatives found in baseline data")
        return

    # Analyze by scenario
    fn_by_scenario = {}
    for fn in false_negatives:
        scenario = fn.get('scenario', 'unknown')
        fn_by_scenario[scenario] = fn_by_scenario.get(scenario, 0) + 1

    # Categorize by error type based on FHRI subscores
    error_types = {
        'Numeric/Directional': 0,
        'Temporal Misalignment': 0,
        'Grounding Failure': 0,
        'Citation Missing': 0,
        'Multiple Issues': 0
    }

    for fn in false_negatives:
        subscores = fn.get('fhri_subscores', {})
        low_scores = []

        # Check which components scored low (< 0.5)
        if subscores.get('N_or_D', 1.0) < 0.5:
            low_scores.append('Numeric/Directional')
        if subscores.get('T', 1.0) < 0.5:
            low_scores.append('Temporal Misalignment')
        if subscores.get('G', 1.0) < 0.5:
            low_scores.append('Grounding Failure')
        if subscores.get('C', 1.0) < 0.5:
            low_scores.append('Citation Missing')

        if len(low_scores) == 0:
            # High-confidence hallucination (all components high but still hallucinated)
            error_types['Grounding Failure'] += 1
        elif len(low_scores) == 1:
            error_types[low_scores[0]] += 1
        else:
            error_types['Multiple Issues'] += 1

    # Create pie chart for error types
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # Left: Error type distribution
    labels = list(error_types.keys())
    sizes = list(error_types.values())
    colors_pie = ['#ff6b6b', '#ffd93d', '#6bcf7f', '#4d96ff', '#b197fc']
    explode = [0.05 if s == max(sizes) else 0 for s in sizes]

    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct*total/100.0))
            return f'{pct:.1f}%%\n(n={val})'
        return my_autopct

    wedges, texts, autotexts = ax1.pie(sizes, explode=explode, labels=labels, colors=colors_pie,
                                        autopct=make_autopct(sizes),
                                        shadow=True, startangle=90)

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)
        autotext.set_fontweight('bold')

    ax1.set_title(f'Error Type Distribution\n(Total FN: {total_fn})',
                 fontsize=14, fontweight='bold', pad=15)

    # Right: Scenario distribution (bar chart)
    scenarios_sorted = sorted(fn_by_scenario.items(), key=lambda x: x[1], reverse=True)
    scenario_names = [s[0].replace('_', ' ').title() for s in scenarios_sorted[:10]]
    scenario_counts = [s[1] for s in scenarios_sorted[:10]]

    bars = ax2.barh(scenario_names, scenario_counts, color='#e74c3c', alpha=0.7, edgecolor='black')

    for bar in bars:
        width = bar.get_width()
        ax2.annotate(f'{int(width)}',
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0),
                    textcoords="offset points",
                    ha='left', va='center',
                    fontsize=10, fontweight='bold')

    ax2.set_xlabel('Number of Missed Hallucinations', fontsize=12, fontweight='bold')
    ax2.set_title('False Negatives by Scenario (Top 10)', fontsize=14, fontweight='bold', pad=15)
    ax2.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    out_path = output_dir / "figure_4_6_error_distribution.png"
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved: {out_path}")
    plt.close()

    # Create Table 4.6: Detailed breakdown
    table_data = []
    for scenario, count in sorted(fn_by_scenario.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_fn) * 100
        table_data.append({
            'Scenario': scenario.replace('_', ' ').title(),
            'FN Count': count,
            'Percentage': f'{percentage:.1f}%',
            'FN Rate': f'{count}/800' if count <= 800 else f'{count}/?'
        })

    df = pd.DataFrame(table_data)

    # Save as CSV
    csv_path = output_dir / "table_4_6_fn_breakdown.csv"
    df.to_csv(csv_path, index=False)
    print(f"[OK] Saved: {csv_path}")

    # Create table visualization
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.axis('tight')
    ax.axis('off')

    table = ax.table(cellText=df.values, colLabels=df.columns,
                    cellLoc='center', loc='center',
                    colWidths=[0.4, 0.2, 0.2, 0.2])

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)

    # Style header
    for i in range(len(df.columns)):
        table[(0, i)].set_facecolor('#e74c3c')
        table[(0, i)].set_text_props(weight='bold', color='white')

    # Alternate row colors
    for i in range(1, len(df) + 1):
        for j in range(len(df.columns)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#f8f9fa')

    plt.title('Table 4.6: False Negative Hallucinations by Scenario',
             fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    out_path = output_dir / "table_4_6_fn_breakdown.png"
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved: {out_path}")
    plt.close()

    # Print summary
    print("\n" + "="*60)
    print("FALSE NEGATIVE ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total False Negatives: {total_fn}")
    print("\nError Type Distribution:")
    for error_type, count in error_types.items():
        print(f"  {error_type}: {count} ({count/total_fn*100:.1f}%)")
    print("\nTop 5 Scenarios with Most FN:")
    for i, (scenario, count) in enumerate(scenarios_sorted[:5], 1):
        print(f"  {i}. {scenario}: {count} ({count/total_fn*100:.1f}%)")
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Generate missing plots for Results chapter")
    parser.add_argument(
        "--baseline",
        type=str,
        default="results/eval_10k_baseline_static.json",
        help="Path to baseline evaluation JSON"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/plots/results_chapter",
        help="Output directory for plots"
    )

    args = parser.parse_args()

    baseline_path = Path(args.baseline)
    output_dir = Path(args.output)

    # Validate baseline file
    if not baseline_path.exists():
        print(f"[ERROR] Baseline file not found: {baseline_path}")
        print("[INFO] Please run evaluation first or provide correct path")
        sys.exit(1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("GENERATING MISSING RESULTS CHAPTER PLOTS")
    print("="*60)

    # Load baseline data
    print(f"\n[INFO] Loading baseline evaluation from {baseline_path}")
    baseline_data = load_json(baseline_path)

    # Generate plots
    print("\n[INFO] Generating visualizations...")
    print("-"*60)

    print("\n[1/5] Creating threshold adjustment heatmap...")
    plot_threshold_heatmap(output_dir)

    print("\n[2/5] Creating multi-scenario PR curves...")
    plot_multi_scenario_pr_curves(output_dir)

    print("\n[3/5] Creating scenario F1 comparison bar chart...")
    plot_scenario_f1_comparison(output_dir)

    print("\n[4/5] Analyzing false negatives and creating error distribution...")
    analyze_false_negatives(baseline_data, output_dir)

    print("\n" + "="*60)
    print(f"[SUCCESS] All plots saved to: {output_dir}")
    print("="*60)
    print("\nGenerated files:")
    print("  1. figure_4_3_threshold_heatmap.png - Threshold optimization heatmap")
    print("  2. figure_4_4_multi_scenario_pr_curves.png - PR curves overlay")
    print("  3. figure_4_5_scenario_f1_comparison.png - F1 scores by scenario")
    print("  4. figure_4_6_error_distribution.png - Error type and scenario distribution")
    print("  5. table_4_6_fn_breakdown.csv - False negative breakdown (CSV)")
    print("  6. table_4_6_fn_breakdown.png - False negative breakdown (table image)")
    print("\nYou can now reference these in your Results chapter (Chapter 4).")


if __name__ == "__main__":
    main()
