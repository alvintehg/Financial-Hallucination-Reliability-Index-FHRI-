# src/fhri_evaluation_logger.py
"""
FHRI Evaluation Logger for Analysis and Visualization.

Logs both raw and adjusted FHRI values, contradiction scores, entropy,
and other metrics for correlation analysis and evaluation.

Features:
- CSV logging of all FHRI computation metrics
- Correlation plot generation (entropy vs contradiction vs FHRI)
- Trend analysis over time
- Export for external analysis tools
"""

import logging
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np

logger = logging.getLogger("fhri_eval")


class FHRIEvaluationLogger:
    """
    Logger for FHRI evaluation metrics with analysis capabilities.
    """

    def __init__(self, log_dir: str = "logs/fhri_eval"):
        """
        Initialize evaluation logger.

        Args:
            log_dir: Directory to store evaluation logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped session log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = self.log_dir / f"fhri_eval_{timestamp}.csv"
        self.json_path = self.log_dir / f"fhri_eval_{timestamp}.json"

        # Initialize CSV
        self.csv_headers = [
            "timestamp",
            "turn_number",
            "query_hash",
            "fhri_raw",
            "fhri_adjusted",
            "fhri_label",
            "entropy_raw",
            "entropy_norm",
            "contradiction_raw",
            "contradiction_smoothed",
            "contradiction_norm",
            "grounding_score",
            "numeric_score",
            "temporal_score",
            "stability_index",
            "weight_entropy",
            "weight_contradiction",
            "weight_grounding",
            "weight_numeric",
            "weight_temporal",
            "retuned",
            "warnings_count",
            "available_components"
        ]

        # Write CSV header
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_headers)
            writer.writeheader()

        # Initialize JSON log
        self.json_log = []

        logger.info(f"FHRI evaluation logger initialized: {self.csv_path}")

    def log_turn(
        self,
        turn_number: int,
        query: str,
        adaptive_fhri_data: Dict[str, Any],
        entropy_raw: Optional[float] = None,
        contradiction_raw: Optional[float] = None
    ):
        """
        Log a single turn's FHRI evaluation metrics.

        Args:
            turn_number: Turn/interaction number
            query: User query text
            adaptive_fhri_data: Full adaptive FHRI result dict
            entropy_raw: Raw semantic entropy value (before normalization)
            contradiction_raw: Raw NLI contradiction score (before smoothing)
        """
        try:
            # Extract data
            subscores = adaptive_fhri_data.get("subscores", {})
            weights = adaptive_fhri_data.get("fhri_weights", {})

            # Compute query hash for drift detection
            query_hash = hash(query.strip().lower())

            # Build CSV row
            row = {
                "timestamp": datetime.now().isoformat(),
                "turn_number": turn_number,
                "query_hash": query_hash,
                "fhri_raw": adaptive_fhri_data.get("fhri"),
                "fhri_adjusted": adaptive_fhri_data.get("fhri"),  # Same for adaptive (already adjusted)
                "fhri_label": adaptive_fhri_data.get("fhri_label"),
                "entropy_raw": entropy_raw,
                "entropy_norm": subscores.get("entropy"),
                "contradiction_raw": contradiction_raw,
                "contradiction_smoothed": adaptive_fhri_data.get("contradiction_smoothed"),
                "contradiction_norm": subscores.get("contradiction"),
                "grounding_score": subscores.get("grounding"),
                "numeric_score": subscores.get("numeric"),
                "temporal_score": subscores.get("temporal"),
                "stability_index": adaptive_fhri_data.get("stability_index"),
                "weight_entropy": weights.get("entropy"),
                "weight_contradiction": weights.get("contradiction"),
                "weight_grounding": weights.get("grounding"),
                "weight_numeric": weights.get("numeric"),
                "weight_temporal": weights.get("temporal"),
                "retuned": adaptive_fhri_data.get("retuned", False),
                "warnings_count": len(adaptive_fhri_data.get("warnings", [])),
                "available_components": "|".join(adaptive_fhri_data.get("available_components", []))
            }

            # Write to CSV
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.csv_headers)
                writer.writerow(row)

            # Add to JSON log (with full query text)
            json_entry = {
                **row,
                "query": query,
                "warnings": adaptive_fhri_data.get("warnings", [])
            }
            self.json_log.append(json_entry)

            # Periodically save JSON (every 10 turns)
            if turn_number % 10 == 0:
                self._save_json()

            logger.debug(f"Logged turn {turn_number}: FHRI={row['fhri_raw']:.3f}, stability={row['stability_index']:.3f}")

        except Exception as e:
            logger.exception(f"Failed to log turn {turn_number}: {e}")

    def _save_json(self):
        """Save JSON log to file."""
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.json_log, f, indent=2)
            logger.debug(f"Saved JSON log: {self.json_path}")
        except Exception as e:
            logger.warning(f"Failed to save JSON log: {e}")

    def log_feedback(self, turn_id: str, rating: int):
        """
        Log user feedback for a specific turn.

        Args:
            turn_id: Unique turn identifier
            rating: User rating (1-5)
        """
        try:
            # Create feedback log file if it doesn't exist
            feedback_path = self.log_dir / "feedback.jsonl"

            feedback_entry = {
                "timestamp": datetime.now().isoformat(),
                "turn_id": turn_id,
                "rating": rating
            }

            # Append to JSONL file
            with open(feedback_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(feedback_entry) + '\n')

            logger.info(f"Logged feedback: turn_id={turn_id}, rating={rating}")

        except Exception as e:
            logger.exception(f"Failed to log feedback: {e}")

    def finalize(self):
        """Finalize logging session and save all data."""
        self._save_json()
        logger.info(f"FHRI evaluation logging finalized: {len(self.json_log)} turns logged")

    def generate_correlation_plot(self, output_path: Optional[str] = None):
        """
        Generate correlation plot: entropy vs contradiction vs FHRI.

        Args:
            output_path: Optional path to save plot image

        Returns:
            Path to saved plot or None if plotting failed
        """
        try:
            import matplotlib.pyplot as plt
            import pandas as pd

            # Load CSV data
            df = pd.read_csv(self.csv_path)

            if len(df) < 3:
                logger.warning("Not enough data for correlation plot (need 3+ turns)")
                return None

            # Create figure with subplots
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            fig.suptitle("FHRI Correlation Analysis", fontsize=16)

            # Plot 1: Entropy vs FHRI
            ax1 = axes[0, 0]
            ax1.scatter(df["entropy_raw"].dropna(), df["fhri_raw"].dropna(), alpha=0.6, c=df["turn_number"], cmap="viridis")
            ax1.set_xlabel("Entropy (raw)")
            ax1.set_ylabel("FHRI")
            ax1.set_title("Entropy vs FHRI")
            ax1.grid(True, alpha=0.3)

            # Plot 2: Contradiction vs FHRI
            ax2 = axes[0, 1]
            ax2.scatter(df["contradiction_smoothed"].dropna(), df["fhri_raw"].dropna(), alpha=0.6, c=df["turn_number"], cmap="viridis")
            ax2.set_xlabel("Contradiction (smoothed)")
            ax2.set_ylabel("FHRI")
            ax2.set_title("Contradiction vs FHRI")
            ax2.grid(True, alpha=0.3)

            # Plot 3: FHRI trend over time
            ax3 = axes[1, 0]
            ax3.plot(df["turn_number"], df["fhri_raw"], marker='o', linestyle='-', label="FHRI")
            ax3.fill_between(df["turn_number"], df["fhri_raw"] - 0.1, df["fhri_raw"] + 0.1, alpha=0.2)
            ax3.set_xlabel("Turn Number")
            ax3.set_ylabel("FHRI")
            ax3.set_title("FHRI Trend Over Time")
            ax3.grid(True, alpha=0.3)
            ax3.legend()

            # Plot 4: Stability index over time
            ax4 = axes[1, 1]
            ax4.plot(df["turn_number"], df["stability_index"], marker='s', linestyle='-', color='green', label="Stability")
            ax4.axhline(y=0.7, color='r', linestyle='--', label="Threshold (0.7)")
            ax4.set_xlabel("Turn Number")
            ax4.set_ylabel("Stability Index")
            ax4.set_title("Stability Index Over Time")
            ax4.grid(True, alpha=0.3)
            ax4.legend()

            plt.tight_layout()

            # Save plot
            if output_path is None:
                output_path = self.log_dir / f"fhri_correlation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()

            logger.info(f"Correlation plot saved to {output_path}")
            return str(output_path)

        except ImportError:
            logger.warning("Matplotlib/pandas not available, skipping plot generation")
            return None
        except Exception as e:
            logger.exception(f"Failed to generate correlation plot: {e}")
            return None

    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate summary statistics report.

        Returns:
            Dict with summary statistics
        """
        try:
            import pandas as pd

            # Load CSV data
            df = pd.read_csv(self.csv_path)

            if len(df) == 0:
                return {"error": "No data available"}

            # Compute statistics
            summary = {
                "total_turns": len(df),
                "fhri_stats": {
                    "mean": float(df["fhri_raw"].mean()),
                    "std": float(df["fhri_raw"].std()),
                    "min": float(df["fhri_raw"].min()),
                    "max": float(df["fhri_raw"].max()),
                    "median": float(df["fhri_raw"].median())
                },
                "stability_stats": {
                    "mean": float(df["stability_index"].mean()),
                    "std": float(df["stability_index"].std()),
                    "min": float(df["stability_index"].min()),
                    "max": float(df["stability_index"].max())
                },
                "retune_count": int(df["retuned"].sum()),
                "warnings_total": int(df["warnings_count"].sum()),
                "correlation": {
                    "entropy_fhri": float(df[["entropy_raw", "fhri_raw"]].corr().iloc[0, 1]) if "entropy_raw" in df.columns else None,
                    "contradiction_fhri": float(df[["contradiction_smoothed", "fhri_raw"]].corr().iloc[0, 1]) if "contradiction_smoothed" in df.columns else None
                }
            }

            logger.info(f"Summary report generated: {summary['total_turns']} turns, "
                       f"mean FHRI={summary['fhri_stats']['mean']:.3f}, "
                       f"mean stability={summary['stability_stats']['mean']:.3f}")

            return summary

        except ImportError:
            logger.warning("Pandas not available, returning minimal summary")
            return {
                "total_turns": len(self.json_log),
                "error": "Pandas not available for detailed statistics"
            }
        except Exception as e:
            logger.exception(f"Failed to generate summary report: {e}")
            return {"error": str(e)}


# Global singleton instance
_default_eval_logger = None


def get_default_eval_logger(log_dir: str = "logs/fhri_eval") -> FHRIEvaluationLogger:
    """Get or create the default FHRI evaluation logger."""
    global _default_eval_logger
    if _default_eval_logger is None:
        _default_eval_logger = FHRIEvaluationLogger(log_dir=log_dir)
        logger.info("Initialized default FHRI evaluation logger")
    return _default_eval_logger


def reset_eval_logger():
    """Reset the singleton evaluation logger (creates new session)."""
    global _default_eval_logger
    if _default_eval_logger:
        _default_eval_logger.finalize()
    _default_eval_logger = None
    logger.info("Reset FHRI evaluation logger")
