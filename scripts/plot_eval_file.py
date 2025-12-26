"""
Plot metrics and confusion matrix from an evaluation JSON file.

Usage:
    python scripts/plot_eval_file.py --input results/eval_10k_optimal_static.json --output-dir results

Defaults:
    --input defaults to results/evaluation_report.json
    --output-dir defaults to the input file's directory.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List

import matplotlib

# Use non-interactive backend for headless environments
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


def build_confusion_matrix(raw_cm: Dict[str, Dict[str, int]], classes: List[str]) -> np.ndarray:
    """Return a dense confusion matrix aligned to the provided class order."""
    matrix = []
    for actual in classes:
        row = []
        for predicted in classes:
            row.append(raw_cm.get(actual, {}).get(predicted, 0))
        matrix.append(row)
    return np.array(matrix, dtype=int)


def plot_metrics(metrics: Dict[str, Dict[str, float]], classes: List[str], output_path: Path, title: str) -> None:
    """Plot per-class precision/recall/F1 bars."""
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
    ax.set_title(title)
    ax.legend()

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
    fig.savefig(output_path, dpi=200)
    print(f"Saved plot to {output_path}")


def plot_confusion(matrix: np.ndarray, classes: List[str], output_path: Path, overall_acc: float) -> None:
    """Plot a labeled confusion matrix heatmap."""
    fig, ax = plt.subplots(figsize=(5.5, 5))
    cmap = plt.cm.Greens
    im = ax.imshow(matrix, cmap=cmap)

    ax.set_xticks(np.arange(len(classes)))
    ax.set_yticks(np.arange(len(classes)))
    ax.set_xticklabels([c.replace("_", " ").title() for c in classes])
    ax.set_yticklabels([c.replace("_", " ").title() for c in classes])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"Confusion Matrix (Accuracy: {overall_acc:.3f})")

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, f"{matrix[i, j]:,}", ha="center", va="center", color="black", fontsize=9)

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    print(f"Saved plot to {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot evaluation metrics and confusion matrix.")
    parser.add_argument(
        "--input",
        "-i",
        default="results/evaluation_report.json",
        help="Path to evaluation JSON file (default: results/evaluation_report.json).",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default=None,
        help="Directory to write plots (defaults to the input file's directory).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report_path = Path(args.input)
    data = json.loads(report_path.read_text())
    metrics = data["metrics"]
    confusion_raw = data.get("confusion_matrix", {})
    meta = data.get("evaluation_metadata", {})

    classes = ["hallucination", "accurate", "contradiction"]
    matrix = build_confusion_matrix(confusion_raw, classes)

    output_dir = Path(args.output_dir) if args.output_dir else report_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    title_suffix = meta.get("evaluation_date", "") or "Evaluation"
    metrics_title = f"FHRI Detection Metrics - {title_suffix}"

    base = output_dir / report_path.stem
    metrics_path = base.with_name(f"{base.name}_metrics.png")
    confusion_path = base.with_name(f"{base.name}_confusion.png")

    plot_metrics(metrics, classes, metrics_path, metrics_title)
    plot_confusion(matrix, classes, confusion_path, metrics["overall"]["accuracy"])


if __name__ == "__main__":
    main()




