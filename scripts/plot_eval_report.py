"""
Generate a simple precision/recall/F1 bar chart from results/evaluation_report.json.

Usage:
    python scripts/plot_eval_report.py
Outputs:
    results/evaluation_report_metrics.png
"""

import json
from pathlib import Path

import matplotlib

# Use non-interactive backend for headless environments
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


def main() -> None:
    report_path = Path("results/evaluation_report.json")
    data = json.loads(report_path.read_text())
    metrics = data["metrics"]

    classes = ["hallucination", "accurate", "contradiction"]
    metric_names = ["precision", "recall", "f1_score"]

    values = [[metrics[c][m] for c in classes] for m in metric_names]
    x = np.arange(len(classes))
    width = 0.25

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    for i, (metric, color) in enumerate(zip(metric_names, colors)):
        ax.bar(x + (i - 1) * width, values[i], width, label=metric.title(), color=color)

    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(x)
    ax.set_xticklabels([c.replace("_", " ").title() for c in classes])
    ax.set_title("FHRI Detection Metrics (full dataset)")
    ax.legend()

    # Annotate bars with values
    for i, metric_vals in enumerate(values):
        for xi, val in zip(x, metric_vals):
            ax.text(
                xi + (i - 1) * width,
                val + 0.015,
                f"{val:.2f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    macro_f1 = metrics["overall"]["macro_f1"]
    ax.axhline(macro_f1, color="gray", linestyle="--", linewidth=1)
    ax.text(len(classes) - 0.5, macro_f1 + 0.01, f"Macro F1: {macro_f1:.2f}", color="gray")

    fig.tight_layout()
    output_path = Path("results/evaluation_report_metrics.png")
    fig.savefig(output_path, dpi=200)
    print(f"Saved plot to {output_path}")


if __name__ == "__main__":
    main()





