"""
FHRI Parameter Fine-Tuning Script

This script optimizes FHRI thresholds and detection logic to maximize
macro F1-score while balancing accurate and hallucination detection.

Usage:
    python scripts/tune_fhri_parameters.py \
        --dataset data/evaluation_dataset.json \
        --output results/fhri_tuning_results.json
"""

import os
import sys
import json
import argparse
import requests
import time
from typing import Dict, List, Any, Tuple
from itertools import product
import numpy as np

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.evaluate_detection import DetectionEvaluator


class FHRIParameterTuner:
    """Fine-tune FHRI parameters to optimize performance."""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.best_params = None
        self.best_score = 0.0
        self.tuning_history = []
        
    def test_backend_connection(self) -> bool:
        """Test if backend server is running."""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def evaluate_with_params(
        self,
        dataset_path: str,
        fhri_threshold: float = 0.65,
        entropy_threshold: float = 2.0,
        contradiction_soft: float = 0.15,
        contradiction_hard: float = 0.40,
        high_risk_floor: float = 0.85,
        use_numeric_check: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate with specific parameter set.
        
        Note: This is a simplified version that post-processes results.
        For full tuning, you'd need to modify backend thresholds.
        """
        # Load dataset
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        samples = dataset.get("samples", [])
        
        # Use existing evaluator but with custom thresholds
        evaluator = DetectionEvaluator(
            backend_url=self.backend_url,
            hallu_threshold=entropy_threshold,
            fhri_threshold=fhri_threshold
        )
        
        # Override thresholds
        evaluator.contradiction_soft_threshold = contradiction_soft
        evaluator.contradiction_hard_threshold = contradiction_hard
        
        # Evaluate
        results = evaluator.evaluate_dataset(dataset_path)
        
        if not results:
            return {"error": "Evaluation failed"}
        
        # Calculate metrics
        metrics = evaluator.calculate_metrics()
        
        # Extract key metrics
        macro_f1 = metrics.get("overall", {}).get("macro_f1", 0.0)
        accurate_f1 = metrics.get("accurate", {}).get("f1_score", 0.0)
        hallucination_f1 = metrics.get("hallucination", {}).get("f1_score", 0.0)
        contradiction_f1 = metrics.get("contradiction", {}).get("f1_score", 0.0)
        overall_accuracy = metrics.get("overall", {}).get("accuracy", 0.0)
        
        return {
            "macro_f1": macro_f1,
            "accurate_f1": accurate_f1,
            "hallucination_f1": hallucination_f1,
            "contradiction_f1": contradiction_f1,
            "overall_accuracy": overall_accuracy,
            "params": {
                "fhri_threshold": fhri_threshold,
                "entropy_threshold": entropy_threshold,
                "contradiction_soft": contradiction_soft,
                "contradiction_hard": contradiction_hard,
                "high_risk_floor": high_risk_floor,
                "use_numeric_check": use_numeric_check
            },
            "metrics": metrics
        }
    
    def grid_search(
        self,
        dataset_path: str,
        fhri_thresholds: List[float] = [0.55, 0.60, 0.65, 0.70, 0.75],
        entropy_thresholds: List[float] = [1.5, 2.0, 2.5, 3.0],
        contradiction_soft: List[float] = [0.10, 0.15, 0.20],
        contradiction_hard: List[float] = [0.35, 0.40, 0.45],
        max_combinations: int = 50
    ) -> Dict[str, Any]:
        """
        Grid search over parameter space.
        
        Limits combinations to avoid excessive runtime.
        """
        print("=" * 70)
        print("FHRI PARAMETER TUNING - GRID SEARCH")
        print("=" * 70)
        print(f"Testing up to {max_combinations} parameter combinations...")
        print("=" * 70)
        
        # Generate all combinations
        all_combinations = list(product(
            fhri_thresholds,
            entropy_thresholds,
            contradiction_soft,
            contradiction_hard
        ))
        
        # Limit combinations
        if len(all_combinations) > max_combinations:
            # Sample evenly
            indices = np.linspace(0, len(all_combinations) - 1, max_combinations, dtype=int)
            all_combinations = [all_combinations[i] for i in indices]
            print(f"Sampling {max_combinations} combinations from {len(list(product(fhri_thresholds, entropy_thresholds, contradiction_soft, contradiction_hard)))} total")
        
        best_result = None
        best_score = 0.0
        
        for i, (fhri_th, ent_th, cont_soft, cont_hard) in enumerate(all_combinations, 1):
            print(f"\n[{i}/{len(all_combinations)}] Testing: FHRI={fhri_th:.2f}, Entropy={ent_th:.1f}, Contradiction=({cont_soft:.2f}, {cont_hard:.2f})")
            
            try:
                result = self.evaluate_with_params(
                    dataset_path,
                    fhri_threshold=fhri_th,
                    entropy_threshold=ent_th,
                    contradiction_soft=cont_soft,
                    contradiction_hard=cont_hard
                )
                
                if "error" in result:
                    print(f"  [ERROR] {result['error']}")
                    continue
                
                # Score: weighted combination of macro F1 and balanced accurate/hallucination F1
                macro_f1 = result["macro_f1"]
                accurate_f1 = result["accurate_f1"]
                hallucination_f1 = result["hallucination_f1"]
                
                # Composite score: prioritize macro F1, but also balance accurate/hallucination
                # Penalize if one is much worse than the other
                balance_penalty = abs(accurate_f1 - hallucination_f1) * 0.1
                composite_score = macro_f1 - balance_penalty
                
                result["composite_score"] = composite_score
                self.tuning_history.append(result)
                
                print(f"  Macro F1: {macro_f1:.4f}, Accurate F1: {accurate_f1:.4f}, Hallucination F1: {hallucination_f1:.4f}")
                print(f"  Composite Score: {composite_score:.4f}")
                
                if composite_score > best_score:
                    best_score = composite_score
                    best_result = result
                    print(f"  ✅ NEW BEST!")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"  [ERROR] {e}")
                continue
        
        self.best_params = best_result
        self.best_score = best_score
        
        return best_result
    
    def print_best_params(self):
        """Print best parameter configuration."""
        if not self.best_params:
            print("\n[ERROR] No best parameters found. Run grid_search first.")
            return
        
        print("\n" + "=" * 70)
        print("BEST PARAMETER CONFIGURATION")
        print("=" * 70)
        
        params = self.best_params["params"]
        print(f"\n📊 Performance:")
        print(f"  Macro F1: {self.best_params['macro_f1']:.4f}")
        print(f"  Accurate F1: {self.best_params['accurate_f1']:.4f}")
        print(f"  Hallucination F1: {self.best_params['hallucination_f1']:.4f}")
        print(f"  Contradiction F1: {self.best_params['contradiction_f1']:.4f}")
        print(f"  Overall Accuracy: {self.best_params['overall_accuracy']:.4f}")
        print(f"  Composite Score: {self.best_params['composite_score']:.4f}")
        
        print(f"\n⚙️  Parameters:")
        print(f"  FHRI Threshold: {params['fhri_threshold']:.2f}")
        print(f"  Entropy Threshold: {params['entropy_threshold']:.1f}")
        print(f"  Contradiction Soft: {params['contradiction_soft']:.2f}")
        print(f"  Contradiction Hard: {params['contradiction_hard']:.2f}")
        print(f"  High Risk Floor: {params['high_risk_floor']:.2f}")
        print(f"  Numeric Check: {params['use_numeric_check']}")
        
        print("\n" + "=" * 70)
    
    def save_results(self, output_path: str):
        """Save tuning results to JSON."""
        if not self.best_params:
            print("[ERROR] No results to save. Run grid_search first.")
            return
        
        report = {
            "tuning_metadata": {
                "backend_url": self.backend_url,
                "tuning_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_combinations_tested": len(self.tuning_history)
            },
            "best_parameters": self.best_params,
            "tuning_history": self.tuning_history
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n[OK] Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Fine-tune FHRI parameters")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/evaluation_dataset.json",
        help="Path to evaluation dataset"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/fhri_tuning_results.json",
        help="Path to save tuning results"
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="http://localhost:8000",
        help="Backend server URL"
    )
    parser.add_argument(
        "--max_combinations",
        type=int,
        default=30,
        help="Maximum number of parameter combinations to test"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.dataset):
        print(f"[ERROR] Dataset not found: {args.dataset}")
        return
    
    tuner = FHRIParameterTuner(backend_url=args.backend)
    
    if not tuner.test_backend_connection():
        print("\n[ERROR] Backend server is not running")
        print("Please start the server with: uvicorn src.server:app --port 8000")
        return
    
    # Run grid search
    best_result = tuner.grid_search(
        args.dataset,
        max_combinations=args.max_combinations
    )
    
    if best_result:
        tuner.print_best_params()
        tuner.save_results(args.output)
        print("\n[OK] Fine-tuning complete!")
        print("\nNext steps:")
        print("1. Update src/fhri_scoring.py with best parameters")
        print("2. Update scripts/evaluate_detection.py with best thresholds")
        print("3. Re-run evaluation to verify improvements")
    else:
        print("\n[ERROR] Fine-tuning failed")


if __name__ == "__main__":
    main()




















