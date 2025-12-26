"""
Run FHRI threshold sweeps per scenario (static mode).

Usage (PowerShell-friendly):
  python scripts/run_scenario_sweeps.py ^
    --dataset data/evaluation_dataset.json ^
    --thresholds 0.50,0.60,0.70,0.80,0.90 ^
    --output_base results/threshold_sweep_per_scenario

Optional: limit to specific scenarios:
  --scenarios numeric_kpi,advice,multi_ticker

Outputs:
  - For each scenario, per-threshold JSON reports under:
      <output_base>/<scenario>/sweep_static_fhri_XX.json
  - For each scenario, a summary CSV:
      <output_base>/<scenario>/sweep_static_summary.csv
"""

import argparse
import os
import sys
from pathlib import Path

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_threshold_sweep import run_once, parse_thresholds  # noqa: E402

try:
    from src.fhri_scoring import SCENARIO_FHRI_THRESHOLDS
except ImportError:
    from fhri_scoring import SCENARIO_FHRI_THRESHOLDS


def write_summary(rows, summary_path: Path):
    import csv

    fieldnames = [
        "threshold",
        "accuracy",
        "macro_f1",
        "hall_precision",
        "hall_recall",
        "hall_f1",
        "accurate_precision",
        "accurate_recall",
        "accurate_f1",
        "contr_precision",
        "contr_recall",
        "contr_f1",
    ]
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def sweep_scenario(dataset_path: Path, scenario: str, thresholds, output_dir: Path):
    rows = []
    for t in thresholds:
        print(f"\n=== Scenario: {scenario} | FHRI threshold: {t:.2f} ===")
        row = run_once(
            dataset_path=dataset_path,
            output_dir=output_dir,
            fhri_threshold=t,
            override_scenarios=False,
            target_scenario=scenario,
        )
        if row:
            rows.append(row)
    if rows:
        write_summary(rows, output_dir / "sweep_static_summary.csv")
        print(f"[OK] Scenario '{scenario}' summary -> {output_dir/'sweep_static_summary.csv'}")
    else:
        print(f"[WARN] No rows for scenario '{scenario}'")


def main():
    parser = argparse.ArgumentParser(description="Per-scenario FHRI threshold sweeps (static mode)")
    parser.add_argument(
        "--dataset",
        default="data/evaluation_dataset.json",
        help="Path to annotated evaluation dataset (JSON)",
    )
    parser.add_argument(
        "--thresholds",
        default="0.50,0.60,0.70,0.80,0.90",
        help="Comma-separated FHRI thresholds to sweep",
    )
    parser.add_argument(
        "--output_base",
        default="results/threshold_sweep_per_scenario",
        help="Base directory for per-scenario outputs",
    )
    parser.add_argument(
        "--scenarios",
        default=None,
        help="Comma-separated scenario ids to sweep; defaults to all in SCENARIO_FHRI_THRESHOLDS",
    )

    args = parser.parse_args()
    dataset_path = Path(args.dataset)
    output_base = Path(args.output_base)
    thresholds = parse_thresholds(args.thresholds)

    if args.scenarios:
        scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip()]
    else:
        scenarios = list(SCENARIO_FHRI_THRESHOLDS.keys())

    for scenario in scenarios:
        safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in scenario)
        out_dir = output_base / safe
        out_dir.mkdir(parents=True, exist_ok=True)
        sweep_scenario(dataset_path, scenario, thresholds, out_dir)


if __name__ == "__main__":
    main()






