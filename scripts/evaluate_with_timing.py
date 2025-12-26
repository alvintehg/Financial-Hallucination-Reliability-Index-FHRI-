"""
Evaluation script with timing and performance tracking.

Records evaluation time and saves comparison data for before/after GPU usage.

Usage:
    python scripts/evaluate_with_timing.py \
        --dataset data/evaluation_dataset.json \
        --output results/evaluation_timed.json
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.evaluate_detection import DetectionEvaluator


def get_gpu_info():
    """Get GPU information if available."""
    try:
        import torch
        if torch.cuda.is_available():
            return {
                "cuda_available": True,
                "gpu_name": torch.cuda.get_device_name(0),
                "cuda_version": torch.version.cuda,
                "pytorch_version": torch.__version__
            }
        else:
            return {
                "cuda_available": False,
                "gpu_name": "N/A",
                "cuda_version": "N/A",
                "pytorch_version": torch.__version__
            }
    except:
        return {
            "cuda_available": False,
            "gpu_name": "N/A",
            "cuda_version": "N/A",
            "pytorch_version": "N/A"
        }


def load_previous_timings(results_dir: str = "results") -> list:
    """Load previous timing records for comparison."""
    timing_file = os.path.join(results_dir, "evaluation_timings.json")
    if os.path.exists(timing_file):
        try:
            with open(timing_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []


def save_timing(results_dir: str, timing_data: dict):
    """Save timing data to history file."""
    timing_file = os.path.join(results_dir, "evaluation_timings.json")
    timings = load_previous_timings(results_dir)
    timings.append(timing_data)
    
    os.makedirs(results_dir, exist_ok=True)
    with open(timing_file, 'w', encoding='utf-8') as f:
        json.dump(timings, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Timing saved to: {timing_file}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate with timing")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/evaluation_dataset.json",
        help="Path to evaluation dataset"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/evaluation_timed.json",
        help="Path to save evaluation report"
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="http://localhost:8000",
        help="Backend server URL"
    )
    parser.add_argument(
        "--fhri_threshold",
        type=float,
        default=0.60,
        help="FHRI threshold"
    )
    
    args = parser.parse_args()
    
    # Get GPU info
    gpu_info = get_gpu_info()
    
    print("=" * 70)
    print("EVALUATION WITH TIMING")
    print("=" * 70)
    print(f"Dataset: {args.dataset}")
    print(f"Backend: {args.backend}")
    print(f"FHRI Threshold: {args.fhri_threshold}")
    print(f"\nGPU Info:")
    print(f"  CUDA Available: {gpu_info['cuda_available']}")
    print(f"  GPU Name: {gpu_info['gpu_name']}")
    print(f"  PyTorch Version: {gpu_info['pytorch_version']}")
    print("=" * 70)
    
    # Record start time
    start_time = time.time()
    start_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n[START] Evaluation started at: {start_datetime}")
    print("-" * 70)
    
    # Run evaluation
    evaluator = DetectionEvaluator(
        backend_url=args.backend,
        fhri_threshold=args.fhri_threshold
    )
    
    results = evaluator.evaluate_dataset(args.dataset)
    
    if not results:
        print("\n[ERROR] Evaluation failed")
        return
    
    # Record end time
    end_time = time.time()
    end_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elapsed_time = end_time - start_time
    
    print("\n" + "-" * 70)
    print(f"[END] Evaluation completed at: {end_datetime}")
    print(f"[TIME] Total elapsed time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    
    # Calculate metrics
    metrics = evaluator.calculate_metrics()
    confusion_matrix = evaluator.generate_confusion_matrix()
    
    # Print report
    evaluator.print_report(metrics, confusion_matrix)
    
    # Save evaluation report
    evaluator.save_report(args.output, metrics, confusion_matrix)
    
    # Prepare timing data
    timing_data = {
        "timestamp": start_datetime,
        "elapsed_seconds": round(elapsed_time, 2),
        "elapsed_minutes": round(elapsed_time / 60, 2),
        "gpu_info": gpu_info,
        "dataset": args.dataset,
        "total_samples": len(results),
        "metrics": {
            "macro_f1": metrics.get("overall", {}).get("macro_f1", 0),
            "accuracy": metrics.get("overall", {}).get("accuracy", 0),
            "accurate_f1": metrics.get("accurate", {}).get("f1_score", 0),
            "hallucination_f1": metrics.get("hallucination", {}).get("f1_score", 0),
            "contradiction_f1": metrics.get("contradiction", {}).get("f1_score", 0)
        },
        "fhri_threshold": args.fhri_threshold
    }
    
    # Load previous timings for comparison
    previous_timings = load_previous_timings()
    
    if previous_timings:
        print("\n" + "=" * 70)
        print("PERFORMANCE COMPARISON")
        print("=" * 70)
        
        # Get most recent previous timing
        last_timing = previous_timings[-1]
        last_time = last_timing.get("elapsed_seconds", 0)
        last_gpu = last_timing.get("gpu_info", {}).get("cuda_available", False)
        
        current_time = elapsed_time
        current_gpu = gpu_info["cuda_available"]
        
        print(f"\nPrevious Evaluation:")
        print(f"  Time: {last_time:.2f} seconds ({last_time/60:.2f} minutes)")
        print(f"  GPU: {'Yes' if last_gpu else 'No'}")
        
        print(f"\nCurrent Evaluation:")
        print(f"  Time: {current_time:.2f} seconds ({current_time/60:.2f} minutes)")
        print(f"  GPU: {'Yes' if current_gpu else 'No'}")
        
        if last_time > 0:
            speedup = last_time / current_time
            time_saved = last_time - current_time
            print(f"\nComparison:")
            print(f"  Speedup: {speedup:.2f}x")
            print(f"  Time saved: {time_saved:.2f} seconds ({time_saved/60:.2f} minutes)")
            
            if current_gpu and not last_gpu:
                print(f"  [INFO] GPU acceleration enabled - {speedup:.2f}x faster!")
            elif not current_gpu and last_gpu:
                print(f"  [WARNING] GPU was available before but not now")
            elif current_gpu and last_gpu:
                print(f"  [INFO] Both runs used GPU")
            else:
                print(f"  [INFO] Both runs used CPU")
    
    # Save timing data
    save_timing("results", timing_data)
    
    print("\n" + "=" * 70)
    print("[OK] Evaluation complete with timing recorded!")
    print("=" * 70)


if __name__ == "__main__":
    main()

















