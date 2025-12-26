"""
Plot Priority 2: FHRI Score Distribution
Shows histograms/violin/box plots of FHRI scores by class, proving that
score distributions separate and supporting the threshold-based approach.

Creates TWO versions:
1. Global threshold (eval_10k_baseline_static.json)
2. Scenario-specific threshold (eval_10k_optimal_static.json)
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict
import sys

def generate_plot(eval_file, output_suffix, title_suffix, threshold_info):
    """Generate FHRI distribution plot for given evaluation file."""

    if not eval_file.exists():
        print(f"[ERROR] File not found: {eval_file}")
        return False

    with open(eval_file, 'r') as f:
        eval_data = json.load(f)

    # Extract FHRI scores by true label
    scores_by_class = defaultdict(list)

    for result in eval_data['detailed_results']:
        true_label = result['true_label']
        fhri_score = result.get('fhri')

        if fhri_score is not None:
            scores_by_class[true_label].append(fhri_score)

    # Map labels to display names
    label_map = {
        'hallucination': 'Hallucination',
        'accurate': 'Accurate',
        'contradiction': 'Contradiction'
    }

    # Prepare data for plotting
    classes = ['hallucination', 'accurate', 'contradiction']
    class_labels = [label_map.get(c, c.title()) for c in classes]
    colors = ['#e74c3c', '#2ecc71', '#f39c12']  # Red, Green, Orange

    # Create figure with subplots
    fig = plt.figure(figsize=(18, 10))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

    # ===== SUBPLOT 1: Violin Plot =====
    ax1 = fig.add_subplot(gs[0, 0])
    positions = np.arange(len(classes))
    violin_data = [scores_by_class[c] for c in classes]

    parts = ax1.violinplot(violin_data, positions=positions, widths=0.6,
                           showmeans=True, showmedians=True)

    # Color the violin plots
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colors[i])
        pc.set_alpha(0.7)
        pc.set_edgecolor('black')
        pc.set_linewidth(1.5)

    # Style the additional elements
    parts['cmeans'].set_color('darkred')
    parts['cmeans'].set_linewidth(2)
    parts['cmedians'].set_color('navy')
    parts['cmedians'].set_linewidth(2)

    ax1.set_xticks(positions)
    ax1.set_xticklabels(class_labels, fontsize=11, fontweight='bold')
    ax1.set_ylabel('FHRI Score', fontsize=12, fontweight='bold')
    ax1.set_title('FHRI Score Distribution by Class (Violin Plot)',
                 fontsize=13, fontweight='bold', pad=15)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    ax1.set_ylim([-0.05, 1.05])

    # Add legend for mean/median
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='darkred', lw=2, label='Mean'),
        Line2D([0], [0], color='navy', lw=2, label='Median')
    ]
    ax1.legend(handles=legend_elements, loc='upper right', fontsize=9)

    # ===== SUBPLOT 2: Box Plot =====
    ax2 = fig.add_subplot(gs[0, 1])
    bp = ax2.boxplot(violin_data, positions=positions, widths=0.5,
                    patch_artist=True, showfliers=True,
                    boxprops=dict(linewidth=1.5),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5),
                    medianprops=dict(color='darkblue', linewidth=2))

    # Color the boxes
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax2.set_xticks(positions)
    ax2.set_xticklabels(class_labels, fontsize=11, fontweight='bold')
    ax2.set_ylabel('FHRI Score', fontsize=12, fontweight='bold')
    ax2.set_title('FHRI Score Distribution by Class (Box Plot)',
                 fontsize=13, fontweight='bold', pad=15)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    ax2.set_ylim([-0.05, 1.05])

    # ===== SUBPLOT 3: Overlapping Histograms =====
    ax3 = fig.add_subplot(gs[1, :])

    bins = np.linspace(0, 1, 30)
    for i, class_name in enumerate(classes):
        data = scores_by_class[class_name]
        ax3.hist(data, bins=bins, alpha=0.6, color=colors[i],
                label=f'{class_labels[i]} (n={len(data)})',
                edgecolor='black', linewidth=0.8)

    # Add threshold lines
    for thresh in threshold_info['values']:
        ax3.axvline(x=thresh, color='gray', linestyle='--', linewidth=1.5, alpha=0.7)
        ax3.text(thresh, ax3.get_ylim()[1] * 0.95, f'T={thresh}',
                rotation=90, verticalalignment='top', fontsize=9,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    ax3.set_xlabel('FHRI Score', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax3.set_title('Overlapping FHRI Score Distributions by Class (Histogram)',
                 fontsize=13, fontweight='bold', pad=15)
    ax3.legend(loc='upper right', fontsize=11, framealpha=0.9)
    ax3.grid(axis='y', alpha=0.3, linestyle='--')
    ax3.set_xlim([0, 1])

    # Add overall title
    fig.suptitle(f'Figure: FHRI Score Distribution by Class ({title_suffix})\n(Demonstrates Score Separation Supporting Threshold-Based Classification)',
                fontsize=15, fontweight='bold', y=0.98)

    # Save
    output_path = Path(f"results/plots/fhri_score_distribution_{output_suffix}.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved FHRI score distribution figure to: {output_path}")

    plt.close()

    # Print statistics
    print("\n" + "=" * 90)
    print(f"FHRI Score Distribution Statistics ({title_suffix})")
    print("=" * 90)
    print(f"{'Class':<15} {'Count':>8} {'Mean':>8} {'Median':>8} {'Std':>8} {'Min':>8} {'Max':>8}")
    print("-" * 90)

    for class_name in classes:
        data = np.array(scores_by_class[class_name])
        label = label_map.get(class_name, class_name.title())

        print(f"{label:<15} {len(data):>8} {np.mean(data):>8.4f} {np.median(data):>8.4f} "
              f"{np.std(data):>8.4f} {np.min(data):>8.4f} {np.max(data):>8.4f}")

    print("=" * 90)

    # Calculate separation metrics
    print("\nSeparation Analysis:")
    print("-" * 90)

    hall_scores = np.array(scores_by_class['hallucination'])
    acc_scores = np.array(scores_by_class['accurate'])
    contr_scores = np.array(scores_by_class['contradiction'])

    mean_diff_hall_acc = abs(np.mean(hall_scores) - np.mean(acc_scores))
    mean_diff_hall_contr = abs(np.mean(hall_scores) - np.mean(contr_scores))
    mean_diff_acc_contr = abs(np.mean(acc_scores) - np.mean(contr_scores))

    print(f"Mean difference (Hallucination vs Accurate):     {mean_diff_hall_acc:.4f}")
    print(f"Mean difference (Hallucination vs Contradiction): {mean_diff_hall_contr:.4f}")
    print(f"Mean difference (Accurate vs Contradiction):      {mean_diff_acc_contr:.4f}")

    # Overlap analysis at thresholds
    print(f"\nThreshold Overlap Analysis:")
    print("-" * 90)
    for thresh in threshold_info['values']:
        hall_below = np.sum(hall_scores < thresh)
        acc_above = np.sum(acc_scores >= thresh)
        acc_below = np.sum(acc_scores < thresh)

        print(f"T={thresh}: Hall below={hall_below}/{len(hall_scores)} ({hall_below/len(hall_scores)*100:.1f}%), "
              f"Acc above={acc_above}/{len(acc_scores)} ({acc_above/len(acc_scores)*100:.1f}%), "
              f"Acc below={acc_below}/{len(acc_scores)} ({acc_below/len(acc_scores)*100:.1f}%)")

    print("=" * 90)
    print(f"\n[OK] FHRI score distribution figure generated successfully for {title_suffix}!\n")

    return True


# Main execution
if __name__ == "__main__":
    # Select which version to generate
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        mode = "both"  # "global", "scenario", or "both"

    success_count = 0

    # Global threshold version (baseline)
    if mode in ["global", "both"]:
        print("\n" + "=" * 90)
        print("GENERATING GLOBAL THRESHOLD VERSION")
        print("=" * 90)
        eval_file = Path("results/eval_10k_baseline_static.json")
        if generate_plot(
            eval_file=eval_file,
            output_suffix="global",
            title_suffix="Global Threshold",
            threshold_info={'values': [0.65]}  # Single global threshold
        ):
            success_count += 1

    # Scenario-specific threshold version (optimal)
    if mode in ["scenario", "both"]:
        print("\n" + "=" * 90)
        print("GENERATING SCENARIO-SPECIFIC THRESHOLD VERSION")
        print("=" * 90)
        eval_file = Path("results/eval_10k_optimal_static.json")
        if generate_plot(
            eval_file=eval_file,
            output_suffix="scenario",
            title_suffix="Scenario-Specific Thresholds",
            threshold_info={'values': [0.55, 0.60, 0.65, 0.70]}  # Range of scenario thresholds
        ):
            success_count += 1

    print("\n" + "=" * 90)
    print(f"SUMMARY: Successfully generated {success_count} figure(s)")
    print("=" * 90)
