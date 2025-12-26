"""
Plot entropy evaluation results comparing baseline vs self-check performance.

This script generates comprehensive visualizations for entropy-based hallucination detection,
creating plots similar to the threshold sweep visualizations.

Usage:
  python scripts/plot_entropy_evaluation.py \
    --baseline results/eval_10k_baseline_static.json \
    --selfcheck results/eval_10k_selfcheck_static.json \
    --output results/plots/entropy_evaluation

Generates:
  - Metric comparison bar charts (Accuracy, Macro F1, per-class metrics)
  - Precision-Recall curves for hallucination detection
  - Confusion matrix heatmaps
  - Performance delta visualizations
  - Entropy distribution analysis
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd


def load_evaluation(file_path: Path) -> Dict[str, Any]:
    """Load evaluation JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def plot_metric_comparison(baseline: Dict, selfcheck: Dict, output_dir: Path):
    """Create bar chart comparing key metrics between baseline and self-check."""
    metrics = {
        'Accuracy': [
            baseline['metrics']['overall']['accuracy'],
            selfcheck['metrics']['overall']['accuracy']
        ],
        'Macro F1': [
            baseline['metrics']['overall']['macro_f1'],
            selfcheck['metrics']['overall']['macro_f1']
        ],
        'Hall Precision': [
            baseline['metrics']['hallucination']['precision'],
            selfcheck['metrics']['hallucination']['precision']
        ],
        'Hall Recall': [
            baseline['metrics']['hallucination']['recall'],
            selfcheck['metrics']['hallucination']['recall']
        ],
        'Hall F1': [
            baseline['metrics']['hallucination']['f1_score'],
            selfcheck['metrics']['hallucination']['f1_score']
        ],
        'Accurate F1': [
            baseline['metrics']['accurate']['f1_score'],
            selfcheck['metrics']['accurate']['f1_score']
        ],
        'Contradiction F1': [
            baseline['metrics']['contradiction']['f1_score'],
            selfcheck['metrics']['contradiction']['f1_score']
        ]
    }

    x = np.arange(len(metrics))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    baseline_vals = [v[0] for v in metrics.values()]
    selfcheck_vals = [v[1] for v in metrics.values()]

    bars1 = ax.bar(x - width/2, baseline_vals, width, label='Baseline (No Entropy)', alpha=0.8)
    bars2 = ax.bar(x + width/2, selfcheck_vals, width, label='Self-Check (With Entropy)', alpha=0.8)

    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}',
                   ha='center', va='bottom', fontsize=8)

    ax.set_ylabel('Score', fontsize=12)
    ax.set_title('Baseline vs Self-Check Entropy: Metric Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics.keys(), rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, 1.1)

    plt.tight_layout()
    out_path = output_dir / "entropy_metric_comparison.png"
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    print(f"[OK] Saved: {out_path}")
    plt.close()


def plot_pr_comparison(baseline: Dict, selfcheck: Dict, output_dir: Path):
    """Create precision-recall comparison for hallucination detection."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Hallucination PR
    baseline_pr = baseline['metrics']['hallucination']
    selfcheck_pr = selfcheck['metrics']['hallucination']

    ax1.scatter([baseline_pr['recall']], [baseline_pr['precision']],
               s=200, alpha=0.7, label='Baseline (No Entropy)', marker='o')
    ax1.scatter([selfcheck_pr['recall']], [selfcheck_pr['precision']],
               s=200, alpha=0.7, label='Self-Check (With Entropy)', marker='s')

    # Add annotations
    ax1.annotate(f"F1={baseline_pr['f1_score']:.3f}",
                xy=(baseline_pr['recall'], baseline_pr['precision']),
                xytext=(10, -10), textcoords='offset points', fontsize=9)
    ax1.annotate(f"F1={selfcheck_pr['f1_score']:.3f}",
                xy=(selfcheck_pr['recall'], selfcheck_pr['precision']),
                xytext=(10, 10), textcoords='offset points', fontsize=9)

    ax1.set_xlabel('Recall', fontsize=12)
    ax1.set_ylabel('Precision', fontsize=12)
    ax1.set_title('Hallucination Detection: Precision-Recall', fontsize=12, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(-0.05, 1.05)
    ax1.set_ylim(-0.05, 1.05)

    # Accurate class PR
    baseline_acc = baseline['metrics']['accurate']
    selfcheck_acc = selfcheck['metrics']['accurate']

    ax2.scatter([baseline_acc['recall']], [baseline_acc['precision']],
               s=200, alpha=0.7, label='Baseline (No Entropy)', marker='o')
    ax2.scatter([selfcheck_acc['recall']], [selfcheck_acc['precision']],
               s=200, alpha=0.7, label='Self-Check (With Entropy)', marker='s')

    ax2.annotate(f"F1={baseline_acc['f1_score']:.3f}",
                xy=(baseline_acc['recall'], baseline_acc['precision']),
                xytext=(10, -10), textcoords='offset points', fontsize=9)
    ax2.annotate(f"F1={selfcheck_acc['f1_score']:.3f}",
                xy=(selfcheck_acc['recall'], selfcheck_acc['precision']),
                xytext=(10, 10), textcoords='offset points', fontsize=9)

    ax2.set_xlabel('Recall', fontsize=12)
    ax2.set_ylabel('Precision', fontsize=12)
    ax2.set_title('Accurate Detection: Precision-Recall', fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(-0.05, 1.05)
    ax2.set_ylim(-0.05, 1.05)

    plt.tight_layout()
    out_path = output_dir / "entropy_pr_comparison.png"
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    print(f"[OK] Saved: {out_path}")
    plt.close()


def plot_confusion_matrices(baseline: Dict, selfcheck: Dict, output_dir: Path):
    """Create side-by-side confusion matrix heatmaps."""
    # Extract confusion matrix data
    def create_cm_array(cm_dict):
        """Convert confusion matrix dict to numpy array."""
        labels = ['hallucination', 'accurate', 'contradiction']
        cm = np.zeros((3, 3))

        for i, true_label in enumerate(labels):
            if true_label in cm_dict:
                for j, pred_label in enumerate(labels):
                    cm[i, j] = cm_dict[true_label].get(pred_label, 0)

        return cm

    baseline_cm = create_cm_array(baseline['confusion_matrix'])
    selfcheck_cm = create_cm_array(selfcheck['confusion_matrix'])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    labels = ['Hallucination', 'Accurate', 'Contradiction']

    # Baseline confusion matrix
    sns.heatmap(baseline_cm, annot=True, fmt='.0f', cmap='Blues',
                xticklabels=labels, yticklabels=labels, ax=ax1, cbar_kws={'label': 'Count'})
    ax1.set_title('Baseline (No Entropy)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('True Label', fontsize=11)
    ax1.set_xlabel('Predicted Label', fontsize=11)

    # Self-check confusion matrix
    sns.heatmap(selfcheck_cm, annot=True, fmt='.0f', cmap='Greens',
                xticklabels=labels, yticklabels=labels, ax=ax2, cbar_kws={'label': 'Count'})
    ax2.set_title('Self-Check (With Entropy)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('True Label', fontsize=11)
    ax2.set_xlabel('Predicted Label', fontsize=11)

    plt.tight_layout()
    out_path = output_dir / "entropy_confusion_matrices.png"
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    print(f"[OK] Saved: {out_path}")
    plt.close()


def plot_performance_delta(baseline: Dict, selfcheck: Dict, output_dir: Path):
    """Create visualization showing performance changes (delta)."""
    metrics = {
        'Accuracy': selfcheck['metrics']['overall']['accuracy'] - baseline['metrics']['overall']['accuracy'],
        'Macro F1': selfcheck['metrics']['overall']['macro_f1'] - baseline['metrics']['overall']['macro_f1'],
        'Hall Precision': selfcheck['metrics']['hallucination']['precision'] - baseline['metrics']['hallucination']['precision'],
        'Hall Recall': selfcheck['metrics']['hallucination']['recall'] - baseline['metrics']['hallucination']['recall'],
        'Hall F1': selfcheck['metrics']['hallucination']['f1_score'] - baseline['metrics']['hallucination']['f1_score'],
        'Accurate F1': selfcheck['metrics']['accurate']['f1_score'] - baseline['metrics']['accurate']['f1_score'],
        'Contr F1': selfcheck['metrics']['contradiction']['f1_score'] - baseline['metrics']['contradiction']['f1_score'],
    }

    fig, ax = plt.subplots(figsize=(10, 6))

    colors = ['green' if v >= 0 else 'red' for v in metrics.values()]
    bars = ax.barh(list(metrics.keys()), list(metrics.values()), color=colors, alpha=0.7)

    # Add value labels
    for i, (metric, value) in enumerate(metrics.items()):
        ax.text(value, i, f'{value:+.3f}', va='center',
               ha='left' if value >= 0 else 'right', fontsize=10, fontweight='bold')

    ax.axvline(x=0, color='black', linewidth=0.8, linestyle='-')
    ax.set_xlabel('Performance Change (Self-Check - Baseline)', fontsize=12)
    ax.set_title('Impact of Entropy on Evaluation Metrics', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')

    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='green', alpha=0.7, label='Improvement'),
                      Patch(facecolor='red', alpha=0.7, label='Degradation')]
    ax.legend(handles=legend_elements)

    plt.tight_layout()
    out_path = output_dir / "entropy_performance_delta.png"
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    print(f"[OK] Saved: {out_path}")
    plt.close()


def plot_entropy_distribution(selfcheck: Dict, output_dir: Path):
    """Plot entropy distribution by true label."""
    # Extract entropy values grouped by true label
    entropies_by_label = {
        'hallucination': [],
        'accurate': [],
        'contradiction': []
    }

    for result in selfcheck['detailed_results']:
        if result.get('entropy') is not None:
            label = result['true_label']
            entropies_by_label[label].append(result['entropy'])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Box plot
    data_to_plot = [entropies_by_label['hallucination'],
                    entropies_by_label['accurate'],
                    entropies_by_label['contradiction']]
    labels = ['Hallucination', 'Accurate', 'Contradiction']

    bp = ax1.boxplot(data_to_plot, labels=labels, patch_artist=True, showmeans=True)

    # Color the boxes
    colors = ['#ff6b6b', '#51cf66', '#ffd93d']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax1.set_ylabel('Entropy Score', fontsize=12)
    ax1.set_title('Entropy Distribution by True Label', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')

    # Histogram with KDE
    for label, color in zip(['hallucination', 'accurate', 'contradiction'], colors):
        if entropies_by_label[label]:
            ax2.hist(entropies_by_label[label], bins=30, alpha=0.5,
                    label=label.capitalize(), color=color, density=True)

    ax2.set_xlabel('Entropy Score', fontsize=12)
    ax2.set_ylabel('Density', fontsize=12)
    ax2.set_title('Entropy Score Distribution', fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    out_path = output_dir / "entropy_distribution.png"
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    print(f"[OK] Saved: {out_path}")
    plt.close()


def plot_fhri_component_comparison(baseline: Dict, selfcheck: Dict, output_dir: Path):
    """Compare FHRI component scores between baseline and self-check."""
    # Sample first 100 items to get component averages
    components = ['N_or_D', 'T', 'E', 'G', 'C']
    baseline_avg = {comp: [] for comp in components}
    selfcheck_avg = {comp: [] for comp in components}

    for result in baseline['detailed_results'][:1000]:
        if result.get('fhri_subscores'):
            for comp in components:
                val = result['fhri_subscores'].get(comp)
                if val is not None:
                    baseline_avg[comp].append(val)

    for result in selfcheck['detailed_results'][:1000]:
        if result.get('fhri_subscores'):
            for comp in components:
                val = result['fhri_subscores'].get(comp)
                if val is not None:
                    selfcheck_avg[comp].append(val)

    # Calculate means
    baseline_means = [np.mean(baseline_avg[c]) if baseline_avg[c] else 0 for c in components]
    selfcheck_means = [np.mean(selfcheck_avg[c]) if selfcheck_avg[c] else 0 for c in components]

    x = np.arange(len(components))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))

    bars1 = ax.bar(x - width/2, baseline_means, width, label='Baseline (No Entropy)', alpha=0.8)
    bars2 = ax.bar(x + width/2, selfcheck_means, width, label='Self-Check (With Entropy)', alpha=0.8)

    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}',
                   ha='center', va='bottom', fontsize=9)

    ax.set_ylabel('Average Score', fontsize=12)
    ax.set_title('FHRI Component Scores Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    component_labels = ['Numeric/Directional', 'Temporal', 'Entropy', 'Grounding', 'Contradiction']
    ax.set_xticklabels(component_labels, rotation=30, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, 1.1)

    plt.tight_layout()
    out_path = output_dir / "entropy_fhri_components.png"
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    print(f"[OK] Saved: {out_path}")
    plt.close()


def create_summary_table(baseline: Dict, selfcheck: Dict, output_dir: Path):
    """Create a summary comparison table and save as image."""
    data = {
        'Metric': [
            'Accuracy',
            'Macro F1',
            'Hall Precision',
            'Hall Recall',
            'Hall F1',
            'Accurate Precision',
            'Accurate Recall',
            'Accurate F1',
            'Contradiction Precision',
            'Contradiction Recall',
            'Contradiction F1',
            'Total Samples',
            'Correct Predictions'
        ],
        'Baseline': [
            f"{baseline['metrics']['overall']['accuracy']:.4f}",
            f"{baseline['metrics']['overall']['macro_f1']:.4f}",
            f"{baseline['metrics']['hallucination']['precision']:.4f}",
            f"{baseline['metrics']['hallucination']['recall']:.4f}",
            f"{baseline['metrics']['hallucination']['f1_score']:.4f}",
            f"{baseline['metrics']['accurate']['precision']:.4f}",
            f"{baseline['metrics']['accurate']['recall']:.4f}",
            f"{baseline['metrics']['accurate']['f1_score']:.4f}",
            f"{baseline['metrics']['contradiction']['precision']:.4f}",
            f"{baseline['metrics']['contradiction']['recall']:.4f}",
            f"{baseline['metrics']['contradiction']['f1_score']:.4f}",
            f"{baseline['metrics']['overall']['total_samples']}",
            f"{baseline['metrics']['overall']['correct_predictions']}"
        ],
        'Self-Check': [
            f"{selfcheck['metrics']['overall']['accuracy']:.4f}",
            f"{selfcheck['metrics']['overall']['macro_f1']:.4f}",
            f"{selfcheck['metrics']['hallucination']['precision']:.4f}",
            f"{selfcheck['metrics']['hallucination']['recall']:.4f}",
            f"{selfcheck['metrics']['hallucination']['f1_score']:.4f}",
            f"{selfcheck['metrics']['accurate']['precision']:.4f}",
            f"{selfcheck['metrics']['accurate']['recall']:.4f}",
            f"{selfcheck['metrics']['accurate']['f1_score']:.4f}",
            f"{selfcheck['metrics']['contradiction']['precision']:.4f}",
            f"{selfcheck['metrics']['contradiction']['recall']:.4f}",
            f"{selfcheck['metrics']['contradiction']['f1_score']:.4f}",
            f"{selfcheck['metrics']['overall']['total_samples']}",
            f"{selfcheck['metrics']['overall']['correct_predictions']}"
        ]
    }

    # Calculate delta
    deltas = []
    for i in range(11):  # Numerical metrics only
        baseline_val = float(data['Baseline'][i])
        selfcheck_val = float(data['Self-Check'][i])
        delta = selfcheck_val - baseline_val
        deltas.append(f"{delta:+.4f}")
    deltas.extend(['—', '—'])  # For count metrics

    data['Delta (Δ)'] = deltas

    # Save as CSV
    df = pd.DataFrame(data)
    csv_path = output_dir / "entropy_comparison_summary.csv"
    df.to_csv(csv_path, index=False)
    print(f"[OK] Saved: {csv_path}")

    # Create table visualization
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.axis('tight')
    ax.axis('off')

    table = ax.table(cellText=df.values, colLabels=df.columns,
                    cellLoc='center', loc='center',
                    colWidths=[0.35, 0.2, 0.2, 0.2])

    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)

    # Style header
    for i in range(len(df.columns)):
        table[(0, i)].set_facecolor('#40466e')
        table[(0, i)].set_text_props(weight='bold', color='white')

    # Color code delta column
    for i in range(1, len(df) + 1):
        if i <= 11:  # Only for numeric metrics
            delta_val = float(deltas[i-1])
            if delta_val > 0:
                table[(i, 3)].set_facecolor('#d4edda')  # Light green
            elif delta_val < 0:
                table[(i, 3)].set_facecolor('#f8d7da')  # Light red

    plt.title('Baseline vs Self-Check: Comprehensive Comparison',
             fontsize=14, fontweight='bold', pad=20)

    plt.tight_layout()
    out_path = output_dir / "entropy_comparison_table.png"
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    print(f"[OK] Saved: {out_path}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Plot entropy evaluation results comparing baseline vs self-check"
    )
    parser.add_argument(
        "--baseline",
        required=True,
        help="Path to baseline evaluation JSON (without entropy)"
    )
    parser.add_argument(
        "--selfcheck",
        required=True,
        help="Path to self-check evaluation JSON (with entropy)"
    )
    parser.add_argument(
        "--output",
        default="results/plots/entropy_evaluation",
        help="Output directory for plots"
    )

    args = parser.parse_args()

    baseline_path = Path(args.baseline)
    selfcheck_path = Path(args.selfcheck)
    output_dir = Path(args.output)

    # Validate inputs
    if not baseline_path.exists():
        print(f"[ERROR] Baseline file not found: {baseline_path}")
        sys.exit(1)

    if not selfcheck_path.exists():
        print(f"[ERROR] Self-check file not found: {selfcheck_path}")
        sys.exit(1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load evaluation data
    print(f"[INFO] Loading baseline evaluation from {baseline_path}")
    baseline = load_evaluation(baseline_path)

    print(f"[INFO] Loading self-check evaluation from {selfcheck_path}")
    selfcheck = load_evaluation(selfcheck_path)

    # Generate plots
    print("\n[INFO] Generating plots...")
    print("-" * 60)

    plot_metric_comparison(baseline, selfcheck, output_dir)
    plot_pr_comparison(baseline, selfcheck, output_dir)
    plot_confusion_matrices(baseline, selfcheck, output_dir)
    plot_performance_delta(baseline, selfcheck, output_dir)
    plot_entropy_distribution(selfcheck, output_dir)
    plot_fhri_component_comparison(baseline, selfcheck, output_dir)
    create_summary_table(baseline, selfcheck, output_dir)

    print("-" * 60)
    print(f"\n[SUCCESS] All plots saved to: {output_dir}")
    print("\nGenerated files:")
    print("  1. entropy_metric_comparison.png - Bar chart comparing key metrics")
    print("  2. entropy_pr_comparison.png - Precision-recall scatter plots")
    print("  3. entropy_confusion_matrices.png - Side-by-side confusion matrices")
    print("  4. entropy_performance_delta.png - Performance change visualization")
    print("  5. entropy_distribution.png - Entropy score distribution by label")
    print("  6. entropy_fhri_components.png - FHRI component comparison")
    print("  7. entropy_comparison_table.png - Comprehensive comparison table")
    print("  8. entropy_comparison_summary.csv - Summary data in CSV format")


if __name__ == "__main__":
    main()
