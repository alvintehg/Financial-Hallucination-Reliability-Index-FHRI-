"""
Regenerate sweep_static_summary.csv files from JSON evaluation results.

This fixes incorrect CSV summaries by re-reading all JSON files.
"""

import json
import csv
from pathlib import Path
import sys

def regenerate_csv_for_scenario(scenario_dir: Path):
    """Regenerate CSV summary from JSON files for a scenario."""

    # Find all JSON files
    json_files = sorted(scenario_dir.glob("sweep_static_fhri_*.json"))

    if not json_files:
        print(f"[WARN] No JSON files found in {scenario_dir.name}")
        return False

    rows = []
    for json_file in json_files:
        # Extract threshold from filename (e.g., sweep_static_fhri_0_65.json -> 0.65)
        threshold_str = json_file.stem.replace("sweep_static_fhri_", "").replace("_", ".")
        try:
            threshold = float(threshold_str)
        except ValueError:
            print(f"[WARN] Could not parse threshold from {json_file.name}")
            continue

        # Read JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        metrics = data.get('metrics', {})

        row = {
            'threshold': threshold,
            'accuracy': metrics.get('overall', {}).get('accuracy', 0),
            'macro_f1': metrics.get('overall', {}).get('macro_f1', 0),
            'hall_precision': metrics.get('hallucination', {}).get('precision', 0),
            'hall_recall': metrics.get('hallucination', {}).get('recall', 0),
            'hall_f1': metrics.get('hallucination', {}).get('f1_score', 0),
            'accurate_precision': metrics.get('accurate', {}).get('precision', 0),
            'accurate_recall': metrics.get('accurate', {}).get('recall', 0),
            'accurate_f1': metrics.get('accurate', {}).get('f1_score', 0),
            'contr_precision': metrics.get('contradiction', {}).get('precision', 0),
            'contr_recall': metrics.get('contradiction', {}).get('recall', 0),
            'contr_f1': metrics.get('contradiction', {}).get('f1_score', 0),
        }
        rows.append(row)

    # Sort by threshold
    rows.sort(key=lambda x: x['threshold'])

    # Write CSV
    csv_path = scenario_dir / "sweep_static_summary.csv"
    fieldnames = [
        'threshold', 'accuracy', 'macro_f1',
        'hall_precision', 'hall_recall', 'hall_f1',
        'accurate_precision', 'accurate_recall', 'accurate_f1',
        'contr_precision', 'contr_recall', 'contr_f1'
    ]

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Regenerated {scenario_dir.name}/sweep_static_summary.csv ({len(rows)} thresholds)")
    return True

def main():
    base_dir = Path("results/threshold_sweep_per_scenario")

    if not base_dir.exists():
        print(f"[ERROR] Directory not found: {base_dir}")
        sys.exit(1)

    print("Regenerating CSV summaries from JSON files...")
    print("=" * 60)

    count = 0
    for scenario_dir in sorted(base_dir.iterdir()):
        if not scenario_dir.is_dir():
            continue

        if regenerate_csv_for_scenario(scenario_dir):
            count += 1

    print("=" * 60)
    print(f"[OK] Regenerated {count} scenario CSV files")

if __name__ == "__main__":
    main()
