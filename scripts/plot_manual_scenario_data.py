"""
Plot Figure 4.3 using manually specified scenario data.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Manual data based on user's table
scenario_data = {
    'fundamentals': {'threshold': 0.65, 'accuracy': 0.942, 'hall_f1': 0.6902, 'accurate_f1': 0.8501, 'contr_f1': 1.0000, 'macro_f1': 0.8468},
    'news': {'threshold': 0.70, 'accuracy': 0.985, 'hall_f1': 1.0000, 'accurate_f1': 1.0000, 'contr_f1': 1.0000, 'macro_f1': 1.0000},
    'crypto': {'threshold': 0.70, 'accuracy': 0.978, 'hall_f1': 1.0000, 'accurate_f1': 1.0000, 'contr_f1': 1.0000, 'macro_f1': 1.0000},
    'default': {'threshold': 0.60, 'accuracy': 1.000, 'hall_f1': 1.0000, 'accurate_f1': 1.0000, 'contr_f1': 1.0000, 'macro_f1': 1.0000},
    'numeric_kpi': {'threshold': 0.65, 'accuracy': 0.965, 'hall_f1': 0.6380, 'accurate_f1': 0.8347, 'contr_f1': 1.0000, 'macro_f1': 0.9234},
    'intraday': {'threshold': 0.65, 'accuracy': 0.958, 'hall_f1': 0.6380, 'accurate_f1': 0.8347, 'contr_f1': 1.0000, 'macro_f1': 0.9156},
    'directional': {'threshold': 0.65, 'accuracy': 0.941, 'hall_f1': 0.6380, 'accurate_f1': 0.8347, 'contr_f1': 1.0000, 'macro_f1': 0.8912},
    'advice': {'threshold': 0.65, 'accuracy': 0.937, 'hall_f1': 1.0000, 'accurate_f1': 1.0000, 'contr_f1': 1.0000, 'macro_f1': 0.8756},
    'regulatory': {'threshold': 0.55, 'accuracy': 0.912, 'hall_f1': 0.6380, 'accurate_f1': 0.8347, 'contr_f1': 1.0000, 'macro_f1': 0.7845},
    'multi_ticker': {'threshold': 0.60, 'accuracy': 0.908, 'hall_f1': 0.6380, 'accurate_f1': 0.8347, 'contr_f1': 1.0000, 'macro_f1': 0.7623},
}

# Sort by macro F1 descending
sorted_scenarios = sorted(scenario_data.items(), key=lambda x: x[1]['macro_f1'], reverse=True)

scenarios = [s[0] for s in sorted_scenarios]
macro_f1 = [s[1]['macro_f1'] for s in sorted_scenarios]
hall_f1 = [s[1]['hall_f1'] for s in sorted_scenarios]
accurate_f1 = [s[1]['accurate_f1'] for s in sorted_scenarios]
contr_f1 = [s[1]['contr_f1'] for s in sorted_scenarios]

# Create figure
fig, ax = plt.subplots(figsize=(16, 8))

# Bar positions
x = np.arange(len(scenarios))
width = 0.20

# Create bars - 4 bars per scenario
bars1 = ax.bar(x - 1.5*width, macro_f1, width, label='Macro F1',
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
        if height > 0.05:  # Only show label if bar is visible
            ax.annotate(f'{height:.2f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 2),
                       textcoords="offset points",
                       ha='center', va='bottom',
                       fontsize=6, rotation=90)

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
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=4, fontsize=11, framealpha=0.9, shadow=True)
ax.set_ylim([0, 1.1])
ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)

# Tight layout
plt.tight_layout()

# Save
output_path = Path("results/plots/figure_4_3_scenario_f1_comparison.png")
output_path.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"[OK] Saved Figure 4.3 to: {output_path}")

plt.close()

# Print summary
print("\n" + "=" * 90)
print("Per-Scenario F1-Score Summary")
print("=" * 90)
print(f"{'Scenario':<15} {'Optimal T':>10} {'Accuracy':>10} {'Hall F1':>10} {'Acc F1':>10} {'Contr F1':>10} {'Macro F1':>10}")
print("-" * 90)

for scenario, data in sorted_scenarios:
    print(f"{scenario:<15} {data['threshold']:>10.2f} {data['accuracy']:>10.1%} "
          f"{data['hall_f1']:>10.4f} {data['accurate_f1']:>10.4f} "
          f"{data['contr_f1']:>10.4f} {data['macro_f1']:>10.4f}")

print("-" * 90)
print(f"{'Weighted Avg':<15} {'-':>10} {'95.2%':>10} {'0.8235':>10} {'0.9034':>10} {'1.0000':>10} {'0.9099':>10}")
print("=" * 90)

print("\n[OK] Figure 4.3 generated successfully!")
