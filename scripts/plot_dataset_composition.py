"""
Plot Priority 1: Dataset Composition Figure
Shows 10K total samples with class split and scenario distribution.
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Define dataset composition
# Total: 10,000 samples
total_samples = 10000

# Class distribution (from your evaluation design)
class_distribution = {
    'Hallucination': 6000,      # 60%
    'Accurate': 2000,           # 20%
    'Contradiction': 2000       # 20%
}

# Scenario distribution (10 scenarios, evenly distributed)
scenarios = [
    'Fundamentals', 'News', 'Crypto', 'Default',
    'Numeric KPI', 'Intraday', 'Directional',
    'Advice', 'Regulatory', 'Multi-ticker'
]
samples_per_scenario = total_samples // len(scenarios)  # 1000 per scenario

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# ===== LEFT PLOT: Class Distribution (Pie Chart) =====
colors_class = ['#e74c3c', '#2ecc71', '#f39c12']  # Red, Green, Orange
explode = (0.05, 0, 0.05)  # Slightly explode Hallucination and Contradiction

wedges, texts, autotexts = ax1.pie(
    class_distribution.values(),
    labels=class_distribution.keys(),
    colors=colors_class,
    autopct=lambda pct: f'{pct:.1f}%\n({int(pct/100*total_samples):,})',
    explode=explode,
    shadow=True,
    startangle=90,
    textprops={'fontsize': 11, 'weight': 'bold'}
)

# Make percentage text white for better contrast
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontsize(12)

ax1.set_title('Class Distribution\n(N = 10,000 samples)',
             fontsize=14, fontweight='bold', pad=20)

# ===== RIGHT PLOT: Scenario Distribution (Bar Chart) =====
colors_scenario = plt.cm.Set3(np.linspace(0, 1, len(scenarios)))

bars = ax2.barh(scenarios, [samples_per_scenario] * len(scenarios),
               color=colors_scenario, edgecolor='black', linewidth=1.2, alpha=0.85)

# Add value labels on bars
for i, bar in enumerate(bars):
    width = bar.get_width()
    ax2.text(width + 30, bar.get_y() + bar.get_height()/2,
            f'{samples_per_scenario:,}',
            ha='left', va='center', fontsize=10, fontweight='bold')

ax2.set_xlabel('Number of Samples', fontsize=12, fontweight='bold')
ax2.set_ylabel('Financial Scenario', fontsize=12, fontweight='bold')
ax2.set_title('Scenario Distribution\n(1,000 samples per scenario)',
             fontsize=14, fontweight='bold', pad=20)
ax2.set_xlim([0, samples_per_scenario + 200])
ax2.grid(axis='x', alpha=0.3, linestyle='--', linewidth=0.5)
ax2.invert_yaxis()  # Highest scenario on top

# Add overall title
fig.suptitle('Figure: Dataset Composition (10K Total Samples)',
            fontsize=16, fontweight='bold', y=0.98)

plt.tight_layout(rect=[0, 0, 1, 0.96])

# Save
output_path = Path("results/plots/dataset_composition.png")
output_path.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"[OK] Saved dataset composition figure to: {output_path}")

plt.close()

# Print summary
print("\n" + "=" * 70)
print("Dataset Composition Summary")
print("=" * 70)
print(f"Total Samples: {total_samples:,}")
print("\nClass Distribution:")
for label, count in class_distribution.items():
    pct = (count / total_samples) * 100
    print(f"  {label:<15}: {count:>6,} ({pct:>5.1f}%)")

print(f"\nScenario Distribution:")
print(f"  Scenarios: {len(scenarios)}")
print(f"  Samples per scenario: {samples_per_scenario:,}")
print(f"  Scenarios: {', '.join(scenarios)}")
print("=" * 70)

print("\n[OK] Dataset composition figure generated successfully!")
