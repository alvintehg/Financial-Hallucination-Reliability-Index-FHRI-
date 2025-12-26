# Entropy Evaluation Results - Visualization Gallery

This folder contains comprehensive visualizations comparing baseline FHRI evaluation (without entropy) vs. self-check evaluation (with entropy component).

## Generated Visualizations

### 1. **entropy_metric_comparison.png**
Bar chart comparing key metrics side-by-side:
- Overall Accuracy
- Macro F1 Score
- Hallucination Precision, Recall, F1
- Accurate F1
- Contradiction F1

**Purpose**: Quick visual comparison of all major performance metrics between the two approaches.

---

### 2. **entropy_pr_comparison.png**
Precision-Recall scatter plots for:
- Hallucination detection (left panel)
- Accurate response detection (right panel)

**Purpose**: Visualize the precision-recall trade-off for each class, with F1 scores annotated.

---

### 3. **entropy_confusion_matrices.png**
Side-by-side confusion matrix heatmaps:
- **Left**: Baseline (no entropy) confusion matrix
- **Right**: Self-check (with entropy) confusion matrix

**Purpose**: Shows classification patterns and misclassifications for each approach.

---

### 4. **entropy_performance_delta.png**
Horizontal bar chart showing performance changes (Δ):
- Green bars = Improvement with entropy
- Red bars = Degradation with entropy

**Purpose**: Highlights which metrics improved or degraded when adding entropy.

---

### 5. **entropy_distribution.png**
Two-panel visualization of entropy scores:
- **Left**: Box plot by true label (hallucination, accurate, contradiction)
- **Right**: Histogram with density overlay

**Purpose**: Analyzes entropy score distributions to understand if entropy differentiates between classes.

---

### 6. **entropy_fhri_components.png**
Bar chart comparing FHRI component scores:
- Numeric/Directional (N_or_D)
- Temporal (T)
- Entropy (E)
- Grounding (G)
- Contradiction (C)

**Purpose**: Shows how adding entropy affects individual FHRI sub-components.

---

### 7. **entropy_comparison_table.png**
Comprehensive comparison table with:
- All metrics for baseline and self-check
- Delta (Δ) column showing changes
- Color-coded cells (green = improvement, red = degradation)

**Purpose**: Detailed reference table for thesis/report inclusion.

---

### 8. **entropy_comparison_summary.csv**
CSV version of the comparison table with all metrics.

**Purpose**: Machine-readable data for further analysis or reporting.

---

## Key Findings Summary

Based on the generated visualizations:

### Performance Impact of Entropy

| Metric | Baseline | Self-Check | Change |
|--------|----------|------------|--------|
| **Accuracy** | 96.00% | 54.82% | **-41.18%** ⬇️ |
| **Macro F1** | 0.9522 | 0.5035 | **-0.4487** ⬇️ |
| **Hall Precision** | 1.0000 | 0.1516 | **-0.8484** ⬇️ |
| **Hall Recall** | 0.8000 | 0.1980 | **-0.6020** ⬇️ |
| **Hall F1** | 0.8889 | 0.1717 | **-0.7172** ⬇️ |

### Analysis

The results show that **adding entropy significantly degraded performance** across all metrics:

1. **Accuracy dropped by 41 percentage points** (96% → 54.82%)
2. **Hallucination detection severely impaired**:
   - Precision fell from 100% to 15.16%
   - Recall dropped from 80% to 19.8%
   - F1 score collapsed from 0.89 to 0.17

3. **Accurate class also degraded**:
   - F1 dropped from 0.97 to 0.66

4. **Contradiction detection partially maintained**:
   - Precision remained at 100%
   - Recall decreased from 100% to 51.9%

### Possible Causes

1. **Entropy Threshold Miscalibration**: The entropy component may be using suboptimal thresholds
2. **Entropy Computation Issues**: The self-check entropy calculation might be producing unreliable scores
3. **Component Weight Imbalance**: Entropy weight in FHRI formula may be too high
4. **Data Quality**: The self-check evaluation may have different data or implementation bugs

### Recommendations

1. **Investigate entropy calculation** - Verify the self-check prompting and entropy scoring logic
2. **Re-calibrate entropy thresholds** - Run threshold sweeps specifically for entropy component
3. **Reduce entropy weight** - Test FHRI with lower entropy contribution (currently 5%)
4. **Validate evaluation data** - Ensure both evaluations used identical test sets and LLM responses

---

## Reproduction

To regenerate these plots:

```bash
python scripts/plot_entropy_evaluation.py \
  --baseline results/eval_10k_baseline_static.json \
  --selfcheck results/eval_10k_selfcheck_static.json \
  --output results/plots/entropy_evaluation
```

## Data Sources

- **Baseline Evaluation**: `results/eval_10k_baseline_static.json` (N=10,000)
- **Self-Check Evaluation**: `results/eval_10k_selfcheck_static.json` (N=10,000)
- **Evaluation Date**: 2025-12-15

---

**Generated**: 2025-12-15
**Script**: `scripts/plot_entropy_evaluation.py`
