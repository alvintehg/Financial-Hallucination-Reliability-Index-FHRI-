"""
Compare Baseline (Entropy) vs FHRI evaluation results.

Usage:
    python scripts/compare_results.py
"""

import json
import os

# Load baseline results
baseline_path = "results/eval_10k_baseline_static.json"
fhri_path = "results/threshold_sweep_static_global_full/sweep_static_fhri_0_70.json"

print("Loading results...")
with open(baseline_path, 'r', encoding='utf-8') as f:
    baseline = json.load(f)

with open(fhri_path, 'r', encoding='utf-8') as f:
    fhri = json.load(f)

print('=' * 80)
print('COMPARISON: Entropy Baseline vs FHRI (10,000 samples)')
print('=' * 80)
print()

# Overall metrics
print('OVERALL PERFORMANCE:')
print('-' * 80)
print(f'{"Metric":<30} {"Baseline (Entropy)":<25} {"FHRI (0.70)":<25}')
print('-' * 80)
acc_base = baseline["metrics"]["overall"]["accuracy"]
acc_fhri = fhri["metrics"]["overall"]["accuracy"]
f1_base = baseline["metrics"]["overall"]["macro_f1"]
f1_fhri = fhri["metrics"]["overall"]["macro_f1"]

print(f'{"Accuracy":<30} {acc_base:<25.2%} {acc_fhri:<25.2%}')
print(f'{"Macro F1":<30} {f1_base:<25.4f} {f1_fhri:<25.4f}')
print()

# Per-class metrics
for label in ['hallucination', 'accurate', 'contradiction']:
    print(f'{label.upper()} DETECTION:')
    print('-' * 80)
    print(f'{"Metric":<30} {"Baseline":<25} {"FHRI":<25}')
    print('-' * 80)

    prec_base = baseline["metrics"][label]["precision"]
    prec_fhri = fhri["metrics"][label]["precision"]
    rec_base = baseline["metrics"][label]["recall"]
    rec_fhri = fhri["metrics"][label]["recall"]
    f1_class_base = baseline["metrics"][label]["f1_score"]
    f1_class_fhri = fhri["metrics"][label]["f1_score"]

    print(f'{"Precision":<30} {prec_base:<25.4f} {prec_fhri:<25.4f}')
    print(f'{"Recall":<30} {rec_base:<25.4f} {rec_fhri:<25.4f}')
    print(f'{"F1-Score":<30} {f1_class_base:<25.4f} {f1_class_fhri:<25.4f}')
    print()

print('=' * 80)
print('CONFUSION MATRICES:')
print('=' * 80)
print()

print('Baseline (Entropy @ 2.0):')
print('-' * 40)
cm_base = baseline["confusion_matrix"]
for true_label in ['hallucination', 'accurate', 'contradiction']:
    row_data = cm_base.get(true_label, {})
    print(f'{true_label:>15}: ', end='')
    for pred_label in ['hallucination', 'accurate', 'contradiction']:
        count = row_data.get(pred_label, 0)
        print(f'{pred_label}={count:<6}', end=' ')
    print()
print()

print('FHRI (Threshold @ 0.70):')
print('-' * 40)
cm_fhri = fhri["confusion_matrix"]
for true_label in ['hallucination', 'accurate', 'contradiction']:
    row_data = cm_fhri.get(true_label, {})
    print(f'{true_label:>15}: ', end='')
    for pred_label in ['hallucination', 'accurate', 'contradiction']:
        count = row_data.get(pred_label, 0)
        print(f'{pred_label}={count:<6}', end=' ')
    print()
print()

print('=' * 80)
print('KEY FINDINGS:')
print('=' * 80)
print()

print('Baseline (Entropy @ 2.0):')
print(f'  - Overall Accuracy: {acc_base:.2%}')
print(f'  - Macro F1: {f1_base:.4f}')
print(f'  - Hallucination F1: {baseline["metrics"]["hallucination"]["f1_score"]:.4f}')
print(f'  - Contradiction F1: {baseline["metrics"]["contradiction"]["f1_score"]:.4f}')
print()

print('FHRI (Threshold @ 0.70):')
print(f'  - Overall Accuracy: {acc_fhri:.2%}')
print(f'  - Macro F1: {f1_fhri:.4f}')
print(f'  - Hallucination F1: {fhri["metrics"]["hallucination"]["f1_score"]:.4f}')
print(f'  - Contradiction F1: {fhri["metrics"]["contradiction"]["f1_score"]:.4f}')
print()

print('WINNER:')
if f1_fhri > f1_base:
    diff = f1_fhri - f1_base
    pct = (diff / f1_base) * 100
    print(f'  FHRI is better by {diff:.4f} Macro F1 (+{pct:.2f}% improvement)')
    print()
    print('  Why FHRI wins:')
    print('  - Better hallucination detection (likely higher precision)')
    print('  - Scenario-aware thresholds')
    print('  - Multi-component scoring (G, N/D, T, C, E)')
else:
    diff = f1_base - f1_fhri
    pct = (diff / f1_fhri) * 100
    print(f'  Baseline is better by {diff:.4f} Macro F1 (+{pct:.2f}% improvement)')
    print()
    print('  Why Baseline wins:')
    print('  - Simpler, faster approach')
    print('  - Better recall on hallucinations')

print()
print('=' * 80)
print('DETAILED ANALYSIS:')
print('=' * 80)
print()

# Hallucination detection comparison
hall_prec_base = baseline["metrics"]["hallucination"]["precision"]
hall_rec_base = baseline["metrics"]["hallucination"]["recall"]
hall_prec_fhri = fhri["metrics"]["hallucination"]["precision"]
hall_rec_fhri = fhri["metrics"]["hallucination"]["recall"]

print('Hallucination Detection:')
if hall_prec_fhri > hall_prec_base:
    print(f'  FHRI has better precision: {hall_prec_fhri:.4f} vs {hall_prec_base:.4f}')
    print(f'  (Fewer false positives - more conservative)')
else:
    print(f'  Baseline has better precision: {hall_prec_base:.4f} vs {hall_prec_fhri:.4f}')

if hall_rec_fhri > hall_rec_base:
    print(f'  FHRI has better recall: {hall_rec_fhri:.4f} vs {hall_rec_base:.4f}')
    print(f'  (Catches more hallucinations)')
else:
    print(f'  Baseline has better recall: {hall_rec_base:.4f} vs {hall_rec_fhri:.4f}')
print()

# Accurate detection comparison
acc_prec_base = baseline["metrics"]["accurate"]["precision"]
acc_rec_base = baseline["metrics"]["accurate"]["recall"]
acc_prec_fhri = fhri["metrics"]["accurate"]["precision"]
acc_rec_fhri = fhri["metrics"]["accurate"]["recall"]

print('Accurate Detection:')
if acc_prec_fhri > acc_prec_base:
    print(f'  FHRI has better precision: {acc_prec_fhri:.4f} vs {acc_prec_base:.4f}')
    print(f'  (Fewer hallucinations marked as accurate)')
else:
    print(f'  Baseline has better precision: {acc_prec_base:.4f} vs {acc_prec_fhri:.4f}')

if acc_rec_fhri > acc_rec_base:
    print(f'  FHRI has better recall: {acc_rec_fhri:.4f} vs {acc_rec_base:.4f}')
    print(f'  (Correctly identifies more accurate responses)')
else:
    print(f'  Baseline has better recall: {acc_rec_base:.4f} vs {acc_rec_fhri:.4f}')
print()

print('=' * 80)
