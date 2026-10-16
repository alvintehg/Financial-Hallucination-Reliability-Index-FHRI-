"""
Evaluation script with checkpoint support for long-running evaluations.

This script extends evaluate_detection.py with:
1. Checkpoint saving after every N samples (default: 100)
2. Resume capability from last checkpoint
3. Support for processing dataset in chunks (e.g., first 5000, then next 5000)
4. Progress tracking and estimated time remaining

Usage:
    # Run first 5000 samples
    python scripts/evaluate_detection_checkpoint.py \
        --dataset data/fhri_evaluation_dataset_full.json \
        --output results/eval_selfcheck_checkpoint.json \
        --mode selfcheck \
        --use_static_answers \
        --start_index 0 \
        --end_index 5000 \
        --checkpoint_interval 100

    # Resume from checkpoint and run next 5000
    python scripts/evaluate_detection_checkpoint.py \
        --dataset data/fhri_evaluation_dataset_full.json \
        --output results/eval_selfcheck_checkpoint.json \
        --mode selfcheck \
        --use_static_answers \
        --start_index 5000 \
        --end_index 10000 \
        --checkpoint_interval 100 \
        --resume
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.evaluate_detection import DetectionEvaluator


class CheckpointEvaluator(DetectionEvaluator):
    """Extended evaluator with checkpoint support."""

    def __init__(self, *args, checkpoint_path: str = None, checkpoint_interval: int = 100, **kwargs):
        super().__init__(*args, **kwargs)
        self.checkpoint_path = checkpoint_path
        self.checkpoint_interval = checkpoint_interval
        self.processed_count = 0
        self.start_time = None

    def save_checkpoint(self, current_index: int, total_samples: int):
        """Save current progress to checkpoint file."""
        if not self.checkpoint_path:
            return

        checkpoint_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_index": current_index,
            "total_samples": total_samples,
            "processed_count": len(self.results),
            "results": self.results,
            "eval_mode": self.eval_mode,
            "fhri_threshold": self.fhri_threshold,
            "hallu_threshold": self.hallu_threshold,
        }

        # Create checkpoint directory if it doesn't exist
        os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)

        # Save to temporary file first, then rename (atomic operation)
        temp_path = self.checkpoint_path + ".tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)

        # Rename to actual checkpoint file
        os.replace(temp_path, self.checkpoint_path)

        elapsed = time.time() - self.start_time if self.start_time else 0
        samples_per_sec = len(self.results) / elapsed if elapsed > 0 else 0
        remaining_samples = total_samples - current_index
        eta_seconds = remaining_samples / samples_per_sec if samples_per_sec > 0 else 0
        eta = str(timedelta(seconds=int(eta_seconds)))

        print(f"\n[CHECKPOINT] Saved at sample {current_index}/{total_samples}")
        print(f"  Progress: {len(self.results)} samples processed")
        print(f"  Speed: {samples_per_sec:.2f} samples/sec")
        print(f"  ETA: {eta}")
        print(f"  Checkpoint: {self.checkpoint_path}\n")

    def load_checkpoint(self) -> dict:
        """Load checkpoint if it exists."""
        if not self.checkpoint_path or not os.path.exists(self.checkpoint_path):
            return None

        try:
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)

            print(f"\n[RESUME] Loading checkpoint from: {self.checkpoint_path}")
            print(f"  Last saved: {checkpoint_data.get('timestamp')}")
            print(f"  Processed: {checkpoint_data.get('processed_count')} samples")
            print(f"  Last index: {checkpoint_data.get('current_index')}\n")

            return checkpoint_data
        except Exception as e:
            print(f"[WARN] Failed to load checkpoint: {e}")
            return None

    def evaluate_dataset_with_checkpoint(
        self,
        dataset_path: str,
        start_index: int = 0,
        end_index: int = None,
        resume: bool = False,
        scenario_filter: list = None
    ):
        """Evaluate dataset with checkpoint support."""

        self.start_time = time.time()

        # Try to resume from checkpoint
        if resume:
            checkpoint_data = self.load_checkpoint()
            if checkpoint_data:
                self.results = checkpoint_data.get("results", [])
                start_index = checkpoint_data.get("current_index", start_index)
                print(f"[RESUME] Continuing from index {start_index}")

        # Load dataset
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
        except Exception as e:
            print(f"[ERROR] Error loading dataset: {e}")
            return []

        samples = dataset.get("samples", [])

        # Flatten if dataset is grouped into lists
        if any(isinstance(item, list) for item in samples):
            flattened = []
            for item in samples:
                if isinstance(item, list):
                    flattened.extend(item)
                else:
                    flattened.append(item)
            samples = flattened

        # Apply range filtering
        if end_index is None:
            end_index = len(samples)
        else:
            end_index = min(end_index, len(samples))

        samples_to_process = samples[start_index:end_index]

        print("=" * 70)
        print("EVALUATION WITH CHECKPOINT SUPPORT")
        print("=" * 70)
        print(f"Dataset: {dataset_path}")
        print(f"Total samples in dataset: {len(samples)}")
        print(f"Processing range: [{start_index}:{end_index}] ({len(samples_to_process)} samples)")
        print(f"Checkpoint interval: {self.checkpoint_interval} samples")
        print(f"Mode: {self.eval_mode.upper()}")
        if self.use_static_answers:
            print("Using: STATIC MODE (stored answers)")
        print("=" * 70)

        # Test backend connection (skip in static mode or selfcheck mode)
        if not self.use_static_answers and self.eval_mode != "selfcheck":
            if not self.test_backend_connection():
                print("\n[ERROR] Cannot proceed: Backend server is not running")
                print("Please start the server with: uvicorn src.server:app --port 8000")
                return []

        # Track pair data for contradiction detection
        pair_data = {}

        # Evaluate each sample
        for i, sample in enumerate(samples_to_process, start=start_index):
            actual_index = i - start_index  # Index within the chunk
            absolute_index = i  # Absolute index in full dataset

            print(f"\n[{absolute_index + 1}/{end_index}] ", end="")

            # Scenario filtering
            if scenario_filter:
                fhri_spec = sample.get("fhri_spec", {})
                scenario_id = fhri_spec.get("scenario_override") or sample.get("scenario_detected")
                if scenario_id not in scenario_filter:
                    print(f"[SKIP] scenario={scenario_id} not in filter {scenario_filter}")
                    continue

            # Handle contradiction pairs
            fhri_spec = sample.get("fhri_spec", {})
            pair_id = fhri_spec.get("contradiction_pair_id")
            sample_id = sample.get("id", "")

            prev_answer = None
            prev_question = None
            true_label = sample.get("ground_truth_label", "")
            question = sample.get("question", "")

            if pair_id:
                if pair_id in pair_data:
                    stored_pairs = pair_data[pair_id]
                    if true_label == "contradiction":
                        for stored_sample_id, stored_question, stored_answer, stored_label in reversed(stored_pairs):
                            if stored_sample_id != sample_id and stored_answer and stored_label == "accurate":
                                prev_answer = stored_answer
                                prev_question = stored_question
                                print(f"[Pair: {pair_id}, using {stored_sample_id}] ", end="")
                                break
                        if not prev_answer:
                            for stored_sample_id, stored_question, stored_answer, stored_label in reversed(stored_pairs):
                                if stored_sample_id != sample_id and stored_answer:
                                    prev_answer = stored_answer
                                    prev_question = stored_question
                                    print(f"[Pair: {pair_id}, using {stored_sample_id} (fallback)] ", end="")
                                    break
                else:
                    pair_data[pair_id] = []

            result = self.evaluate_sample(sample, prev_answer=prev_answer, prev_question=prev_question)

            if result:
                status = "[OK] Correct" if result["correct"] else "[X] Incorrect"
                print(f"  {status}: True={result['true_label']}, Predicted={result['predicted_label']}")

                # Store answer for contradiction pairs
                if pair_id:
                    llm_answer = result.get("llm_answer", "")
                    pair_data[pair_id].append((sample_id, question, llm_answer, true_label))

            # Save checkpoint at intervals
            if (absolute_index + 1) % self.checkpoint_interval == 0:
                self.save_checkpoint(absolute_index + 1, end_index)

        # Final checkpoint
        self.save_checkpoint(end_index, end_index)

        elapsed = time.time() - self.start_time
        print(f"\n[COMPLETE] Processed {len(samples_to_process)} samples in {elapsed:.2f} seconds")
        print(f"  Average: {len(samples_to_process) / elapsed:.2f} samples/sec")

        return self.results


def main():
    parser = argparse.ArgumentParser(description="Evaluate with checkpoint support")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/fhri_evaluation_dataset_full.json",
        help="Path to annotated evaluation dataset (JSON)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/evaluation_checkpoint.json",
        help="Path to save evaluation report"
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Path to checkpoint file (default: output_path + '.checkpoint')"
    )
    parser.add_argument(
        "--checkpoint_interval",
        type=int,
        default=100,
        help="Save checkpoint every N samples (default: 100)"
    )
    parser.add_argument(
        "--start_index",
        type=int,
        default=0,
        help="Start processing from this index (default: 0)"
    )
    parser.add_argument(
        "--end_index",
        type=int,
        default=None,
        help="End processing at this index (default: end of dataset)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint"
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="http://localhost:8000",
        help="Backend server URL"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=2.0,
        help="Hallucination entropy threshold"
    )
    parser.add_argument(
        "--fhri_threshold",
        type=float,
        default=0.70,
        help="FHRI threshold for accurate label"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["baseline", "fhri", "selfcheck"],
        default="fhri",
        help="Evaluation mode: 'baseline' (entropy-only), 'fhri' (with FHRI scoring), or 'selfcheck' (DeepSeek self-consistency)"
    )
    parser.add_argument(
        "--selfcheck_k",
        type=int,
        default=3,
        help="Number of self-consistency samples for selfcheck mode"
    )
    parser.add_argument(
        "--selfcheck_model",
        type=str,
        default="deepseek-chat",
        help="DeepSeek model name for selfcheck mode"
    )
    parser.add_argument(
        "--use_static_answers",
        action="store_true",
        help="Use stored answers from dataset instead of querying backend (static mode)"
    )

    args = parser.parse_args()

    # Set checkpoint path
    checkpoint_path = args.checkpoint
    if checkpoint_path is None:
        checkpoint_path = args.output + ".checkpoint"

    # Check if dataset exists
    if not os.path.exists(args.dataset):
        print(f"[ERROR] Dataset not found at {args.dataset}")
        return

    # Configure evaluation
    use_fhri = args.mode == "fhri"
    print(f"\nEvaluation mode: {args.mode.upper()}")
    if args.mode == "baseline":
        print("  (Baseline: entropy-only detection, FHRI disabled)")
    elif args.mode == "fhri":
        print("  (FHRI: full reliability scoring enabled)")
    elif args.mode == "selfcheck":
        print(f"  (SelfCheck: DeepSeek self-consistency, k={args.selfcheck_k}, model={args.selfcheck_model})")

    # Run evaluation with checkpoints
    evaluator = CheckpointEvaluator(
        backend_url=args.backend,
        hallu_threshold=args.threshold,
        fhri_threshold=args.fhri_threshold,
        use_static_answers=args.use_static_answers,
        checkpoint_path=checkpoint_path,
        checkpoint_interval=args.checkpoint_interval
    )
    evaluator.use_fhri = use_fhri
    evaluator.eval_mode = args.mode
    evaluator.selfcheck_k = args.selfcheck_k
    evaluator.selfcheck_model = args.selfcheck_model

    results = evaluator.evaluate_dataset_with_checkpoint(
        args.dataset,
        start_index=args.start_index,
        end_index=args.end_index,
        resume=args.resume
    )

    if not results:
        print("\n[ERROR] Evaluation failed or no results obtained")
        return

    # Calculate metrics
    metrics = evaluator.calculate_metrics()
    confusion_matrix = evaluator.generate_confusion_matrix()

    # Print and save report
    evaluator.print_report(metrics, confusion_matrix)
    evaluator.save_report(args.output, metrics, confusion_matrix)

    print(f"\n[OK] Evaluation complete!")
    print(f"  Total samples evaluated: {len(results)}")
    print(f"  Overall accuracy: {metrics['overall']['accuracy']:.2%}")
    print(f"  Macro F1-Score: {metrics['overall']['macro_f1']:.4f}")
    print(f"  Final report: {args.output}")
    print(f"  Checkpoint: {checkpoint_path}")


if __name__ == "__main__":
    main()
