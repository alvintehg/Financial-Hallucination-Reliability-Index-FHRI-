"""
Generate visualizations from evaluation results.

This script creates plots and charts from evaluation reports:
1. Precision-Recall curves for detection performance
2. Confusion matrices (heatmaps)
3. Latency distribution histograms
4. F1-score comparisons across classes
5. ROC curves (if threshold sweeping is performed)

Usage:
    python scripts/generate_plots.py --evaluation results/evaluation_report.json --latency results/latency_report.json --output results/plots/
"""

import os
import sys
import json
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional

# Try to import plotting libraries
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("Warning: matplotlib or seaborn not installed. Install with: pip install matplotlib seaborn")


class PlotGenerator:
    """Generates plots from evaluation results."""

    def __init__(self, output_dir: str = "results/plots"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        if PLOTTING_AVAILABLE:
            # Set style
            sns.set_style("whitegrid")
            plt.rcParams['figure.figsize'] = (10, 6)
            plt.rcParams['font.size'] = 10

    def plot_confusion_matrix(
        self,
        confusion_matrix: Dict[str, Dict[str, int]],
        classes: List[str],
        output_path: str = None
    ):
        """Plot confusion matrix as heatmap."""
        if not PLOTTING_AVAILABLE:
            print("⚠ Skipping confusion matrix plot (matplotlib not available)")
            return

        # Convert dict to numpy array
        matrix = np.zeros((len(classes), len(classes)))
        for i, true_class in enumerate(classes):
            for j, pred_class in enumerate(classes):
                matrix[i, j] = confusion_matrix.get(true_class, {}).get(pred_class, 0)

        # Create heatmap
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            matrix,
            annot=True,
            fmt='g',
            cmap='Blues',
            xticklabels=classes,
            yticklabels=classes,
            cbar_kws={'label': 'Count'}
        )
        plt.xlabel('Predicted Label')
        plt.ylabel('True Label')
        plt.title('Confusion Matrix - Detection Performance')
        plt.tight_layout()

        if output_path is None:
            output_path = os.path.join(self.output_dir, "confusion_matrix.png")

        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Saved confusion matrix: {output_path}")

    def plot_metrics_comparison(
        self,
        metrics: Dict[str, Any],
        output_path: str = None
    ):
        """Plot precision, recall, F1 comparison across classes."""
        if not PLOTTING_AVAILABLE:
            print("⚠ Skipping metrics comparison plot (matplotlib not available)")
            return

        classes = [k for k in metrics.keys() if k != "overall"]
        if not classes:
            print("⚠ No class metrics found")
            return

        # Extract metrics
        precision_vals = [metrics[cls]["precision"] for cls in classes]
        recall_vals = [metrics[cls]["recall"] for cls in classes]
        f1_vals = [metrics[cls]["f1_score"] for cls in classes]

        # Create grouped bar chart
        x = np.arange(len(classes))
        width = 0.25

        fig, ax = plt.subplots(figsize=(10, 6))
        bars1 = ax.bar(x - width, precision_vals, width, label='Precision', color='#3498db')
        bars2 = ax.bar(x, recall_vals, width, label='Recall', color='#2ecc71')
        bars3 = ax.bar(x + width, f1_vals, width, label='F1-Score', color='#e74c3c')

        ax.set_xlabel('Class')
        ax.set_ylabel('Score')
        ax.set_title('Detection Metrics by Class')
        ax.set_xticks(x)
        ax.set_xticklabels(classes, rotation=15, ha='right')
        ax.legend()
        ax.set_ylim([0, 1.1])
        ax.grid(axis='y', alpha=0.3)

        # Add value labels on bars
        def add_labels(bars):
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom',
                            fontsize=8)

        add_labels(bars1)
        add_labels(bars2)
        add_labels(bars3)

        plt.tight_layout()

        if output_path is None:
            output_path = os.path.join(self.output_dir, "metrics_comparison.png")

        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Saved metrics comparison: {output_path}")

    def plot_latency_histogram(
        self,
        latency_data: List[float],
        bins: int = 20,
        output_path: str = None
    ):
        """Plot latency distribution histogram."""
        if not PLOTTING_AVAILABLE:
            print("⚠ Skipping latency histogram (matplotlib not available)")
            return

        fig, ax = plt.subplots(figsize=(10, 6))

        # Create histogram
        n, bins_edges, patches = ax.hist(
            latency_data,
            bins=bins,
            color='#3498db',
            alpha=0.7,
            edgecolor='black'
        )

        # Add mean and median lines
        mean_val = np.mean(latency_data)
        median_val = np.median(latency_data)

        ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.1f}ms')
        ax.axvline(median_val, color='green', linestyle='--', linewidth=2, label=f'Median: {median_val:.1f}ms')

        # Add p95 line
        p95 = np.percentile(latency_data, 95)
        ax.axvline(p95, color='orange', linestyle='--', linewidth=2, label=f'P95: {p95:.1f}ms')

        ax.set_xlabel('Latency (ms)')
        ax.set_ylabel('Frequency')
        ax.set_title('Response Latency Distribution')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        if output_path is None:
            output_path = os.path.join(self.output_dir, "latency_histogram.png")

        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Saved latency histogram: {output_path}")

    def plot_latency_percentiles(
        self,
        stats: Dict[str, Any],
        output_path: str = None
    ):
        """Plot latency percentiles as bar chart."""
        if not PLOTTING_AVAILABLE:
            print("⚠ Skipping latency percentiles plot (matplotlib not available)")
            return

        if "total_latency" not in stats:
            print("⚠ No latency statistics found")
            return

        lat = stats["total_latency"]

        percentiles = ['Min', 'P50\n(Median)', 'Mean', 'P95', 'P99', 'Max']
        values = [
            lat.get('min_ms', 0),
            lat.get('p50_ms', 0),
            lat.get('mean_ms', 0),
            lat.get('p95_ms', 0),
            lat.get('p99_ms', 0),
            lat.get('max_ms', 0)
        ]

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(percentiles, values, color=['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6', '#34495e'])

        ax.set_ylabel('Latency (ms)')
        ax.set_title('Latency Percentiles')
        ax.grid(axis='y', alpha=0.3)

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.1f}ms',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=9)

        plt.tight_layout()

        if output_path is None:
            output_path = os.path.join(self.output_dir, "latency_percentiles.png")

        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Saved latency percentiles: {output_path}")

    def plot_f1_scores_summary(
        self,
        metrics: Dict[str, Any],
        output_path: str = None
    ):
        """Plot F1 scores with overall macro F1."""
        if not PLOTTING_AVAILABLE:
            print("⚠ Skipping F1 summary plot (matplotlib not available)")
            return

        classes = [k for k in metrics.keys() if k != "overall"]
        if not classes:
            print("⚠ No class metrics found")
            return

        f1_vals = [metrics[cls]["f1_score"] for cls in classes]
        macro_f1 = metrics.get("overall", {}).get("macro_f1", 0)

        # Add macro F1 to the plot
        classes.append("Macro\nAverage")
        f1_vals.append(macro_f1)

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12']
        bars = ax.bar(classes, f1_vals, color=colors[:len(classes)])

        ax.set_ylabel('F1-Score')
        ax.set_title('F1-Score Performance Summary')
        ax.set_ylim([0, 1.1])
        ax.grid(axis='y', alpha=0.3)
        ax.axhline(y=0.8, color='green', linestyle=':', alpha=0.5, label='Target: 0.80')
        ax.legend()

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.3f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=10,
                        fontweight='bold')

        plt.tight_layout()

        if output_path is None:
            output_path = os.path.join(self.output_dir, "f1_summary.png")

        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Saved F1 summary: {output_path}")

    def plot_success_rate(
        self,
        stats: Dict[str, Any],
        output_path: str = None
    ):
        """Plot success rate pie chart."""
        if not PLOTTING_AVAILABLE:
            print("⚠ Skipping success rate plot (matplotlib not available)")
            return

        successful = stats.get("successful_requests", 0)
        failed = stats.get("failed_requests", 0)
        total = stats.get("total_requests", 0)

        if total == 0:
            print("⚠ No request data found")
            return

        fig, ax = plt.subplots(figsize=(8, 6))

        sizes = [successful, failed]
        labels = [f'Successful\n({successful})', f'Failed\n({failed})']
        colors = ['#2ecc71', '#e74c3c']
        explode = (0.05, 0)

        wedges, texts, autotexts = ax.pie(
            sizes,
            explode=explode,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            shadow=True,
            startangle=90
        )

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(12)
            autotext.set_fontweight('bold')

        ax.set_title(f'Request Success Rate\nTotal Requests: {total}')

        plt.tight_layout()

        if output_path is None:
            output_path = os.path.join(self.output_dir, "success_rate.png")

        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Saved success rate: {output_path}")

    def plot_fhri_subscores_by_label(
        self,
        detailed_results: List[Dict[str, Any]],
        output_path: str = None
    ):
        """Plot mean FHRI sub-scores for accurate vs hallucinated labels."""
        if not PLOTTING_AVAILABLE:
            print("⚠ Skipping FHRI subscores plot (matplotlib not available)")
            return

        # Group results by true label
        accurate_subscores = {"G": [], "N_or_D": [], "T": [], "C": [], "E": []}
        hallu_subscores = {"G": [], "N_or_D": [], "T": [], "C": [], "E": []}

        for result in detailed_results:
            true_label = result.get("true_label", "")
            subscores = result.get("fhri_subscores", {})

            target = accurate_subscores if true_label == "accurate" else hallu_subscores

            for key in accurate_subscores.keys():
                score = subscores.get(key)
                if score is not None:
                    target[key].append(score)

        # Compute means
        import numpy as np
        accurate_means = {k: np.mean(v) if v else 0 for k, v in accurate_subscores.items()}
        hallu_means = {k: np.mean(v) if v else 0 for k, v in hallu_subscores.items()}

        # Plot
        fig, ax = plt.subplots(figsize=(10, 6))

        components = list(accurate_means.keys())
        x = np.arange(len(components))
        width = 0.35

        bars1 = ax.bar(x - width/2, [accurate_means[c] for c in components], width, label='Accurate', color='#2ecc71')
        bars2 = ax.bar(x + width/2, [hallu_means[c] for c in components], width, label='Hallucinated', color='#e74c3c')

        ax.set_xlabel('FHRI Component')
        ax.set_ylabel('Mean Score')
        ax.set_title('FHRI Sub-Scores: Accurate vs Hallucinated Answers')
        ax.set_xticks(x)
        ax.set_xticklabels(components)
        ax.legend()
        ax.set_ylim([0, 1.1])
        ax.grid(axis='y', alpha=0.3)

        # Add value labels
        for bar in bars1:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=8)

        for bar in bars2:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom',
                        fontsize=8)

        plt.tight_layout()

        if output_path is None:
            output_path = os.path.join(self.output_dir, "fhri_subscores_by_label.png")

        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Saved FHRI subscores by label: {output_path}")

    def plot_fhri_vs_entropy_comparison(
        self,
        detailed_results: List[Dict[str, Any]],
        output_path: str = None
    ):
        """Plot comparison of FHRI and entropy for detecting hallucinations."""
        if not PLOTTING_AVAILABLE:
            print("⚠ Skipping FHRI vs entropy comparison (matplotlib not available)")
            return

        # Extract data
        import numpy as np
        accurate_fhri = []
        accurate_entropy = []
        hallu_fhri = []
        hallu_entropy = []

        for result in detailed_results:
            true_label = result.get("true_label", "")
            fhri = result.get("fhri")
            entropy = result.get("entropy")

            if fhri is not None and entropy is not None:
                if true_label == "accurate":
                    accurate_fhri.append(fhri)
                    accurate_entropy.append(entropy)
                elif true_label == "hallucination":
                    hallu_fhri.append(fhri)
                    hallu_entropy.append(entropy)

        # Create scatter plot
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.scatter(accurate_entropy, accurate_fhri, alpha=0.6, s=100, c='#2ecc71', label='Accurate', edgecolors='black')
        ax.scatter(hallu_entropy, hallu_fhri, alpha=0.6, s=100, c='#e74c3c', label='Hallucination', edgecolors='black', marker='s')

        ax.set_xlabel('Entropy Score')
        ax.set_ylabel('FHRI Score')
        ax.set_title('FHRI vs Entropy: Accurate vs Hallucinated Answers')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path is None:
            output_path = os.path.join(self.output_dir, "fhri_vs_entropy.png")

        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Saved FHRI vs entropy comparison: {output_path}")

    def plot_scenario_performance_comparison(
        self,
        scenario_analysis: Dict[str, Any],
        output_path: Optional[str] = None
    ):
        """
        Plot per-scenario performance comparison: Entropy-only vs FHRI.

        Shows Precision, Recall, and F1-score for each scenario.
        """
        if not PLOTTING_AVAILABLE:
            print("Plotting not available")
            return

        by_scenario = scenario_analysis.get("by_scenario", {})
        if not by_scenario:
            print("No scenario data available")
            return

        # Prepare data
        scenarios = []
        entropy_f1 = []
        fhri_f1 = []
        entropy_pr = []
        fhri_pr = []
        entropy_rc = []
        fhri_rc = []

        for scenario_id, data in by_scenario.items():
            scenario_name = data.get("scenario_name", scenario_id)
            scenarios.append(scenario_name)

            entropy_metrics = data.get("entropy_only", {})
            fhri_metrics = data.get("fhri", {})

            entropy_f1.append(entropy_metrics.get("f1", 0.0))
            fhri_f1.append(fhri_metrics.get("f1", 0.0))
            entropy_pr.append(entropy_metrics.get("precision", 0.0))
            fhri_pr.append(fhri_metrics.get("precision", 0.0))
            entropy_rc.append(entropy_metrics.get("recall", 0.0))
            fhri_rc.append(fhri_metrics.get("recall", 0.0))

        # Create figure with 3 subplots
        fig, axes = plt.subplots(3, 1, figsize=(12, 14))

        x = np.arange(len(scenarios))
        width = 0.35

        # Precision comparison
        axes[0].bar(x - width/2, entropy_pr, width, label='Entropy-only', alpha=0.8, color='#f59e0b')
        axes[0].bar(x + width/2, fhri_pr, width, label='FHRI', alpha=0.8, color='#10b981')
        axes[0].set_ylabel('Precision', fontsize=12, fontweight='bold')
        axes[0].set_title('Precision by Scenario: Entropy-only vs FHRI', fontsize=14, fontweight='bold')
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(scenarios, rotation=45, ha='right')
        axes[0].legend()
        axes[0].grid(axis='y', alpha=0.3)
        axes[0].set_ylim(0, 1.0)

        # Recall comparison
        axes[1].bar(x - width/2, entropy_rc, width, label='Entropy-only', alpha=0.8, color='#f59e0b')
        axes[1].bar(x + width/2, fhri_rc, width, label='FHRI', alpha=0.8, color='#10b981')
        axes[1].set_ylabel('Recall', fontsize=12, fontweight='bold')
        axes[1].set_title('Recall by Scenario: Entropy-only vs FHRI', fontsize=14, fontweight='bold')
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(scenarios, rotation=45, ha='right')
        axes[1].legend()
        axes[1].grid(axis='y', alpha=0.3)
        axes[1].set_ylim(0, 1.0)

        # F1-Score comparison
        axes[2].bar(x - width/2, entropy_f1, width, label='Entropy-only', alpha=0.8, color='#f59e0b')
        axes[2].bar(x + width/2, fhri_f1, width, label='FHRI', alpha=0.8, color='#10b981')
        axes[2].set_ylabel('F1-Score', fontsize=12, fontweight='bold')
        axes[2].set_title('F1-Score by Scenario: Entropy-only vs FHRI', fontsize=14, fontweight='bold')
        axes[2].set_xlabel('Scenario', fontsize=12, fontweight='bold')
        axes[2].set_xticks(x)
        axes[2].set_xticklabels(scenarios, rotation=45, ha='right')
        axes[2].legend()
        axes[2].grid(axis='y', alpha=0.3)
        axes[2].set_ylim(0, 1.0)

        plt.tight_layout()

        if output_path is None:
            output_path = os.path.join(self.output_dir, "scenario_performance_comparison.png")

        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Saved scenario performance comparison: {output_path}")

    def plot_scenario_f1_improvement(
        self,
        scenario_analysis: Dict[str, Any],
        output_path: Optional[str] = None
    ):
        """
        Plot F1 improvement (FHRI - Entropy) by scenario.
        """
        if not PLOTTING_AVAILABLE:
            print("Plotting not available")
            return

        by_scenario = scenario_analysis.get("by_scenario", {})
        if not by_scenario:
            print("No scenario data available")
            return

        # Prepare data
        scenarios = []
        improvements = []
        counts = []

        for scenario_id, data in by_scenario.items():
            scenario_name = data.get("scenario_name", scenario_id)
            scenarios.append(scenario_name)
            improvements.append(data.get("f1_improvement", 0.0))
            counts.append(data.get("count", 0))

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))

        colors = ['#10b981' if imp >= 0 else '#ef4444' for imp in improvements]
        bars = ax.barh(scenarios, improvements, alpha=0.8, color=colors)

        # Add count labels
        for i, (bar, count) in enumerate(zip(bars, counts)):
            width = bar.get_width()
            label_x = width + 0.01 if width >= 0 else width - 0.01
            ha = 'left' if width >= 0 else 'right'
            ax.text(label_x, bar.get_y() + bar.get_height()/2,
                   f'n={count}', ha=ha, va='center', fontsize=9, color='gray')

        ax.set_xlabel('F1-Score Improvement (FHRI - Entropy)', fontsize=12, fontweight='bold')
        ax.set_title('FHRI Performance Improvement by Scenario', fontsize=14, fontweight='bold')
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()

        if output_path is None:
            output_path = os.path.join(self.output_dir, "scenario_f1_improvement.png")

        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Saved scenario F1 improvement: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate plots from evaluation results")
    parser.add_argument(
        "--evaluation",
        type=str,
        help="Path to evaluation report JSON"
    )
    parser.add_argument(
        "--latency",
        type=str,
        help="Path to latency report JSON"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        help="Path to scenario analysis JSON (from evaluate_by_scenario.py)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/plots",
        help="Output directory for plots"
    )

    args = parser.parse_args()

    if not PLOTTING_AVAILABLE:
        print("\n✗ Error: matplotlib and seaborn are required for plotting")
        print("Install with: pip install matplotlib seaborn")
        return

    if not args.evaluation and not args.latency and not args.scenario:
        print("\n✗ Error: Please provide at least one of --evaluation, --latency, or --scenario")
        print("\nUsage:")
        print("  python scripts/generate_plots.py --evaluation results/evaluation_report.json")
        print("  python scripts/generate_plots.py --latency results/latency_report.json")
        print("  python scripts/generate_plots.py --scenario results/scenario_analysis.json")
        print("  python scripts/generate_plots.py --evaluation results/evaluation_report.json --scenario results/scenario_analysis.json")
        return

    print("=" * 60)
    print("GENERATING PLOTS")
    print("=" * 60)

    plotter = PlotGenerator(output_dir=args.output)

    # Load and plot evaluation results
    if args.evaluation:
        if not os.path.exists(args.evaluation):
            print(f"✗ Evaluation report not found: {args.evaluation}")
        else:
            print(f"\nProcessing evaluation report: {args.evaluation}")
            with open(args.evaluation, 'r', encoding='utf-8') as f:
                eval_data = json.load(f)

            metrics = eval_data.get("metrics", {})
            confusion_matrix = eval_data.get("confusion_matrix", {})
            detailed_results = eval_data.get("detailed_results", [])

            if metrics:
                classes = [k for k in metrics.keys() if k != "overall"]
                if confusion_matrix and classes:
                    plotter.plot_confusion_matrix(confusion_matrix, classes)
                if classes:
                    plotter.plot_metrics_comparison(metrics)
                    plotter.plot_f1_scores_summary(metrics)

            # FHRI-specific plots
            if detailed_results:
                plotter.plot_fhri_subscores_by_label(detailed_results)
                plotter.plot_fhri_vs_entropy_comparison(detailed_results)

    # Load and plot scenario analysis
    if args.scenario:
        if not os.path.exists(args.scenario):
            print(f"✗ Scenario analysis not found: {args.scenario}")
        else:
            print(f"\nProcessing scenario analysis: {args.scenario}")
            with open(args.scenario, 'r', encoding='utf-8') as f:
                scenario_data = json.load(f)

            plotter.plot_scenario_performance_comparison(scenario_data)
            plotter.plot_scenario_f1_improvement(scenario_data)

    # Load and plot latency results
    if args.latency:
        if not os.path.exists(args.latency):
            print(f"✗ Latency report not found: {args.latency}")
        else:
            print(f"\nProcessing latency report: {args.latency}")
            with open(args.latency, 'r', encoding='utf-8') as f:
                latency_data = json.load(f)

            stats = latency_data.get("statistics", {})
            measurements = latency_data.get("detailed_measurements", [])

            if stats:
                plotter.plot_latency_percentiles(stats)
                plotter.plot_success_rate(stats)

            # Extract latency values for histogram
            if measurements:
                latencies = [
                    m["total_latency_ms"]
                    for m in measurements
                    if m.get("status") == "success" and m.get("total_latency_ms")
                ]
                if latencies:
                    plotter.plot_latency_histogram(latencies)

    print("\n" + "=" * 60)
    print(f"✓ Plots saved to: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
