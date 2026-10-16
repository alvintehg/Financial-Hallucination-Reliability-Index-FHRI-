"""
Run a static FHRI threshold sweep in one shot.

This script:
  - Runs scripts/evaluate_detection.DetectionEvaluator in static mode (use_static_answers)
  - Sweeps a list of FHRI thresholds
  - Saves per-threshold JSON reports
  - Writes a CSV summary of key metrics (precision/recall/F1/accuracy)

Usage (PowerShell-friendly):
  python scripts/run_threshold_sweep.py ^
    --dataset data/evaluation_dataset.json ^
    --output_dir results/threshold_sweep_static ^
    --thresholds 0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90

Notes:
  - No backend required (static mode).
  - Adjust the thresholds list as needed.
"""

import argparse
import csv
import os
import sys
from pathlib import Path

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate_detection import DetectionEvaluator  # noqa: E402
try:
    from src.fhri_scoring import SCENARIO_FHRI_THRESHOLDS
except ImportError:
    from fhri_scoring import SCENARIO_FHRI_THRESHOLDS


def run_once(
    dataset_path: Path,
    output_dir: Path,
    fhri_threshold: float,
    override_scenarios: bool = False,
    target_scenario: str = None,
):
    """Run a single static evaluation at a given FHRI threshold."""
    evaluator = DetectionEvaluator(
        backend_url="http://localhost:8000",
        hallu_threshold=2.0,
        fhri_threshold=fhri_threshold,
        use_static_answers=True,
    )
    evaluator.use_fhri = True  # keep FHRI on
    evaluator.override_scenario_thresholds = override_scenarios

    if target_scenario:
        # Override only the target scenario threshold; keep others default
        evaluator.scenario_thresholds = SCENARIO_FHRI_THRESHOLDS.copy()
        evaluator.scenario_thresholds[target_scenario] = fhri_threshold

    # If a target scenario is provided, only evaluate samples whose scenario matches
    scenario_filter = [target_scenario] if target_scenario else None
    results = evaluator.evaluate_dataset(str(dataset_path), scenario_filter=scenario_filter)
    if not results:
        return None

    metrics = evaluator.calculate_metrics()
    confusion = evaluator.generate_confusion_matrix()

    tag = f"{fhri_threshold:.2f}".replace(".", "_")
    report_path = output_dir / f"sweep_static_fhri_{tag}.json"
    evaluator.save_report(str(report_path), metrics, confusion)

    row = {
        "threshold": fhri_threshold,
        "accuracy": metrics.get("overall", {}).get("accuracy"),
        "macro_f1": metrics.get("overall", {}).get("macro_f1"),
        "hall_precision": metrics.get("hallucination", {}).get("precision"),
        "hall_recall": metrics.get("hallucination", {}).get("recall"),
        "hall_f1": metrics.get("hallucination", {}).get("f1_score"),
        "accurate_precision": metrics.get("accurate", {}).get("precision"),
        "accurate_recall": metrics.get("accurate", {}).get("recall"),
        "accurate_f1": metrics.get("accurate", {}).get("f1_score"),
        "contr_precision": metrics.get("contradiction", {}).get("precision"),
        "contr_recall": metrics.get("contradiction", {}).get("recall"),
        "contr_f1": metrics.get("contradiction", {}).get("f1_score"),
    }
    return row


def parse_thresholds(thresholds_str: str):
    return [float(x.strip()) for x in thresholds_str.split(",") if x.strip()]


def main():
    parser = argparse.ArgumentParser(description="Static FHRI threshold sweep")
    parser.add_argument(
        "--dataset",
        default="data/evaluation_dataset.json",
        help="Path to annotated evaluation dataset (JSON)",
    )
    parser.add_argument(
        "--output_dir",
        default="results/threshold_sweep_static",
        help="Directory to write per-threshold reports and summary CSV",
    )
    parser.add_argument(
        "--thresholds",
        default="0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90",
        help="Comma-separated FHRI thresholds to sweep",
    )
    parser.add_argument(
        "--override_scenario_thresholds",
        action="store_true",
        help="Use the global threshold for all scenarios (ignore per-scenario thresholds) in static mode",
    )
    parser.add_argument(
        "--target_scenario",
        type=str,
        default=None,
        help="If set, only this scenario's threshold is overridden/swept; others remain default",
    )

    args = parser.parse_args()
    dataset_path = Path(args.dataset)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    thresholds = parse_thresholds(args.thresholds)
    rows = []

    for t in thresholds:
        print(f"\n=== FHRI threshold: {t:.2f} ===")
        row = run_once(
            dataset_path,
            output_dir,
            t,
            override_scenarios=args.override_scenario_thresholds,
            target_scenario=args.target_scenario,
        )
        if row:
            rows.append(row)

    # Write summary CSV
    summary_path = output_dir / "sweep_static_summary.csv"
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
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"\n[OK] Summary written to: {summary_path}")
    print(f"[OK] Per-threshold reports in: {output_dir}")


if __name__ == "__main__":
    main()

