"""
Plot per-scenario sweep results (hallucination PR and macro F1).

Assumes you have run run_scenario_sweeps.py and have:
  results/threshold_sweep_per_scenario/<scenario>/sweep_static_summary.csv

Usage:
  python scripts/plot_scenario_sweeps.py \
    --base results/threshold_sweep_per_scenario

Outputs per scenario:
  - sweep_static_pr_<scenario>.png
  - sweep_static_macro_f1_<scenario>.png
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def plot_pr(csv_path: Path):
    df = pd.read_csv(csv_path)
    plt.figure()
    plt.plot(df["hall_recall"], df["hall_precision"], marker="o")
    for r, p, t in zip(df["hall_recall"], df["hall_precision"], df["threshold"]):
        plt.text(r, p, f"{t:.2f}", fontsize=8)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(f"FHRI static sweep ({csv_path.parent.name})")
    plt.grid(True)
    out = csv_path.parent / f"sweep_static_pr_{csv_path.parent.name}.png"
    plt.savefig(out, dpi=200)
    print(f"[OK] {out}")


def plot_macro_f1(csv_path: Path):
    df = pd.read_csv(csv_path)
    plt.figure()
    plt.plot(df["threshold"], df["macro_f1"], marker="o")
    for t, f1 in zip(df["threshold"], df["macro_f1"]):
        plt.text(t, f1, f"{t:.2f}", fontsize=8)
    plt.xlabel("Threshold")
    plt.ylabel("Macro F1")
    plt.title(f"Macro F1 ({csv_path.parent.name})")
    plt.grid(True)
    out = csv_path.parent / f"sweep_static_macro_f1_{csv_path.parent.name}.png"
    plt.savefig(out, dpi=200)
    print(f"[OK] {out}")


def main():
    parser = argparse.ArgumentParser(description="Plot per-scenario sweep results")
    parser.add_argument(
        "--base",
        default="results/threshold_sweep_per_scenario",
        help="Base directory containing per-scenario sweep outputs",
    )
    args = parser.parse_args()

    base = Path(args.base)
    if not base.exists():
        print(f"[ERROR] Base directory not found: {base}")
        sys.exit(1)

    scenarios = [p for p in base.iterdir() if p.is_dir()]
    if not scenarios:
        print(f"[WARN] No scenario folders found under {base}")
        sys.exit(0)

    for scen_dir in scenarios:
        csv_path = scen_dir / "sweep_static_summary.csv"
        if not csv_path.exists():
            print(f"[WARN] Missing CSV for {scen_dir.name}, skipping")
            continue
        try:
            plot_pr(csv_path)
            plot_macro_f1(csv_path)
        except Exception as e:
            print(f"[WARN] Failed to plot {scen_dir.name}: {e}")


if __name__ == "__main__":
    main()






