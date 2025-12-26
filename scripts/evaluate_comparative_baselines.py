"""
Comparative Baseline Evaluation Script

This script evaluates different hallucination detection methods:
1. Entropy-only (Semantic Entropy baseline)
2. NLI-only (Contradiction detection baseline)
3. RAG-only (Retrieval faithfulness baseline)
4. FHRI-full (Full multi-component fusion)

Usage:
    python scripts/evaluate_comparative_baselines.py --dataset data/evaluation_dataset.json --output results/comparative_baselines.json
"""

import os
import sys
import json
import argparse
import requests
import time
from typing import Dict, List, Any
from collections import defaultdict
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.evaluate_detection import DetectionEvaluator


class ComparativeBaselineEvaluator:
    """Evaluates multiple baseline methods for comparison."""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.results_by_method = {
            "entropy_only": [],
            "nli_only": [],
            "rag_only": [],
            "fhri_full": []
        }
        
    def test_backend_connection(self) -> bool:
        """Test if backend server is running."""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def query_with_method(self, question: str, prev_answer: str = None, 
                         method: str = "fhri_full") -> Dict[str, Any]:
        """
        Query chatbot with specific detection method.
        
        Methods:
        - entropy_only: Only use entropy for hallucination detection
        - nli_only: Only use NLI contradiction for detection
        - rag_only: Only use grounding/retrieval faithfulness
        - fhri_full: Full FHRI with all components
        """
        payload = {
            "text": question,
            "k": 5,
            "provider": "auto",
        }
        
        if prev_answer:
            payload["prev_assistant_turn"] = prev_answer
        
        # Configure method-specific flags
        if method == "entropy_only":
            payload["use_entropy"] = True
            payload["use_nli"] = False
            payload["use_fhri"] = False
        elif method == "nli_only":
            payload["use_entropy"] = False
            payload["use_nli"] = True
            payload["use_fhri"] = False
        elif method == "rag_only":
            payload["use_entropy"] = False
            payload["use_nli"] = False
            payload["use_fhri"] = False  # We'll compute grounding manually
        else:  # fhri_full
            payload["use_entropy"] = True
            payload["use_nli"] = True
            payload["use_fhri"] = True
        
        try:
            response = requests.post(
                f"{self.backend_url}/ask",
                json=payload,
                timeout=90
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  [ERROR] Query failed: {e}")
            return None
    
    def extract_detection_scores(self, response: Dict[str, Any], method: str) -> Dict[str, Any]:
        """Extract relevant scores based on detection method."""
        result = {
            "entropy": response.get("entropy"),
            "contradiction_score": response.get("contradiction_score"),
            "fhri": None,
            "grounding_score": None,
            "is_hallucination_detected": False,
            "is_contradiction_detected": False
        }
        
        # Extract FHRI components if available
        meta = response.get("meta", {})
        if meta:
            result["fhri"] = meta.get("fhri")
            fhri_subscores = meta.get("fhri_subscores", {})
            result["grounding_score"] = fhri_subscores.get("grounding")
        
        # Method-specific detection logic
        if method == "entropy_only":
            # Use entropy threshold (2.0) for hallucination detection
            entropy = result["entropy"]
            if entropy is not None:
                result["is_hallucination_detected"] = entropy > 2.0
        
        elif method == "nli_only":
            # Use NLI contradiction threshold (0.15 soft, 0.40 hard)
            contradiction = result["contradiction_score"]
            if contradiction is not None:
                result["is_contradiction_detected"] = contradiction >= 0.15
        
        elif method == "rag_only":
            # Use grounding score threshold (0.6) for hallucination detection
            grounding = result["grounding_score"]
            if grounding is not None:
                result["is_hallucination_detected"] = grounding < 0.6
        
        else:  # fhri_full
            # Use existing FHRI logic from DetectionEvaluator
            result["is_hallucination_detected"] = response.get("is_hallucination", False)
            contradiction = result["contradiction_score"]
            if contradiction is not None:
                result["is_contradiction_detected"] = contradiction >= 0.15
        
        return result
    
    def predict_label(self, scores: Dict[str, Any], method: str, 
                     fhri_threshold: float = 0.65) -> str:
        """Predict label based on method and scores."""
        # Priority: contradiction > hallucination > accurate
        
        if scores["is_contradiction_detected"]:
            return "contradiction"
        
        if scores["is_hallucination_detected"]:
            return "hallucination"
        
        # For FHRI-full, check FHRI threshold
        if method == "fhri_full" and scores["fhri"] is not None:
            if scores["fhri"] > fhri_threshold:
                return "accurate"
            else:
                return "hallucination"
        
        # For other methods, if no detection, assume accurate
        return "accurate"
    
    def evaluate_sample(self, sample: Dict[str, Any], prev_answer: str = None) -> Dict[str, Any]:
        """Evaluate a single sample with all methods."""
        sample_id = sample.get("id", "unknown")
        question = sample.get("question", "")
        true_label = sample.get("ground_truth_label", sample.get("your_annotation", ""))
        
        if not true_label or true_label not in ["accurate", "hallucination", "contradiction"]:
            return None
        
        results = {
            "sample_id": sample_id,
            "question": question,
            "true_label": true_label
        }
        
        # Evaluate with each method
        for method in ["entropy_only", "nli_only", "rag_only", "fhri_full"]:
            print(f"  [{method}] ", end="", flush=True)
            
            response = self.query_with_method(question, prev_answer, method)
            if not response:
                results[method] = {"error": "Query failed"}
                continue
            
            scores = self.extract_detection_scores(response, method)
            predicted_label = self.predict_label(scores, method)
            
            results[method] = {
                "predicted_label": predicted_label,
                "correct": predicted_label == true_label,
                **scores
            }
            
            self.results_by_method[method].append({
                "sample_id": sample_id,
                "true_label": true_label,
                "predicted_label": predicted_label,
                "correct": predicted_label == true_label,
                **scores
            })
            
            time.sleep(0.3)  # Rate limiting
        
        return results
    
    def evaluate_dataset(self, dataset_path: str) -> Dict[str, Any]:
        """Evaluate entire dataset with all methods."""
        print("=" * 70)
        print("COMPARATIVE BASELINE EVALUATION")
        print("=" * 70)
        print(f"Dataset: {dataset_path}")
        print(f"Backend: {self.backend_url}")
        print("Methods: Entropy-only, NLI-only, RAG-only, FHRI-full")
        print("=" * 70)
        
        if not self.test_backend_connection():
            print("\n[ERROR] Backend server is not running")
            return {}
        
        # Load dataset
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
        except Exception as e:
            print(f"[ERROR] Error loading dataset: {e}")
            return {}
        
        samples = dataset.get("samples", [])
        print(f"\nFound {len(samples)} samples")
        print("=" * 70)
        
        # Track contradiction pairs
        pair_data = {}
        
        for i, sample in enumerate(samples, 1):
            print(f"\n[{i}/{len(samples)}] {sample.get('id', 'unknown')}: {sample.get('question', '')[:60]}...")
            
            # Handle contradiction pairs
            fhri_spec = sample.get("fhri_spec", {})
            pair_id = fhri_spec.get("contradiction_pair_id")
            prev_answer = None
            
            if pair_id and pair_id in pair_data:
                stored_pairs = pair_data[pair_id]
                for stored_id, stored_q, stored_a, stored_label in reversed(stored_pairs):
                    if stored_label == "accurate" and stored_a:
                        prev_answer = stored_a
                        break
            
            result = self.evaluate_sample(sample, prev_answer)
            
            if result and pair_id:
                # Store answer for future pairs
                for method in ["entropy_only", "nli_only", "rag_only", "fhri_full"]:
                    if method in result and "fhri" in result[method]:
                        # Use FHRI-full answer if available
                        response = self.query_with_method(sample.get("question", ""), prev_answer, "fhri_full")
                        if response and response.get("answer"):
                            if pair_id not in pair_data:
                                pair_data[pair_id] = []
                            pair_data[pair_id].append((
                                sample.get("id", ""),
                                sample.get("question", ""),
                                response.get("answer", ""),
                                sample.get("ground_truth_label", "")
                            ))
                            break
        
        return self.calculate_comparative_metrics()
    
    def calculate_comparative_metrics(self) -> Dict[str, Any]:
        """Calculate metrics for each method."""
        metrics = {}
        
        for method, results in self.results_by_method.items():
            if not results:
                continue
            
            classes = ["hallucination", "accurate", "contradiction"]
            method_metrics = {}
            
            for cls in classes:
                tp = sum(1 for r in results if r["true_label"] == cls and r["predicted_label"] == cls)
                fp = sum(1 for r in results if r["true_label"] != cls and r["predicted_label"] == cls)
                fn = sum(1 for r in results if r["true_label"] == cls and r["predicted_label"] != cls)
                
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
                
                method_metrics[cls] = {
                    "precision": round(precision, 4),
                    "recall": round(recall, 4),
                    "f1_score": round(f1, 4),
                    "tp": tp,
                    "fp": fp,
                    "fn": fn,
                    "support": tp + fn
                }
            
            # Overall metrics
            correct = sum(1 for r in results if r["correct"])
            overall_accuracy = correct / len(results) if results else 0.0
            macro_f1 = sum(m["f1_score"] for m in method_metrics.values()) / len(method_metrics) if method_metrics else 0.0
            
            metrics[method] = {
                "overall": {
                    "accuracy": round(overall_accuracy, 4),
                    "macro_f1": round(macro_f1, 4),
                    "total_samples": len(results),
                    "correct_predictions": correct
                },
                "per_class": method_metrics
            }
        
        return metrics
    
    def print_comparative_report(self, metrics: Dict[str, Any]):
        """Print comparative report."""
        print("\n" + "=" * 70)
        print("COMPARATIVE BASELINE RESULTS")
        print("=" * 70)
        
        methods = ["entropy_only", "nli_only", "rag_only", "fhri_full"]
        method_names = {
            "entropy_only": "Entropy-Only",
            "nli_only": "NLI-Only",
            "rag_only": "RAG-Only",
            "fhri_full": "FHRI-Full"
        }
        
        # Overall comparison table
        print("\n📊 Overall Performance Comparison:")
        print(f"\n{'Method':<20} {'Accuracy':<12} {'Macro F1':<12} {'Total Samples':<15}")
        print("-" * 70)
        
        for method in methods:
            if method in metrics:
                m = metrics[method]["overall"]
                print(f"{method_names[method]:<20} {m['accuracy']:<12.4f} {m['macro_f1']:<12.4f} {m['total_samples']:<15}")
        
        # Per-class comparison
        print("\n📋 Per-Class F1-Score Comparison:")
        classes = ["hallucination", "accurate", "contradiction"]
        print(f"\n{'Method':<20} {'Hallucination F1':<18} {'Accurate F1':<15} {'Contradiction F1':<18}")
        print("-" * 70)
        
        for method in methods:
            if method in metrics:
                per_class = metrics[method]["per_class"]
                row = [method_names[method]]
                for cls in classes:
                    f1 = per_class.get(cls, {}).get("f1_score", 0.0)
                    row.append(f"{f1:.4f}")
                print("  ".join(f"{r:<20}" for r in row))
        
        print("\n" + "=" * 70)
    
    def save_report(self, output_path: str, metrics: Dict[str, Any]):
        """Save comparative report to JSON."""
        report = {
            "evaluation_metadata": {
                "backend_url": self.backend_url,
                "evaluation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "methods": ["entropy_only", "nli_only", "rag_only", "fhri_full"]
            },
            "metrics": metrics,
            "detailed_results": self.results_by_method
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n[OK] Report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate comparative baselines")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/evaluation_dataset.json",
        help="Path to evaluation dataset"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/comparative_baselines.json",
        help="Path to save report"
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="http://localhost:8000",
        help="Backend server URL"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.dataset):
        print(f"[ERROR] Dataset not found: {args.dataset}")
        return
    
    evaluator = ComparativeBaselineEvaluator(backend_url=args.backend)
    metrics = evaluator.evaluate_dataset(args.dataset)
    
    if metrics:
        evaluator.print_comparative_report(metrics)
        evaluator.save_report(args.output, metrics)
        print("\n[OK] Comparative evaluation complete!")
    else:
        print("\n[ERROR] Evaluation failed")


if __name__ == "__main__":
    main()




















