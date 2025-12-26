"""
Ablation Study Evaluation Script

This script evaluates FHRI with components removed one by one to measure
each component's contribution to overall performance.

Ablation variants:
1. FHRI-full (all components)
2. FHRI - Entropy (remove entropy component)
3. FHRI - Contradiction (remove contradiction component)
4. FHRI - Grounding (remove grounding component)
5. FHRI - Numeric (remove numeric component)
6. FHRI - Temporal (remove temporal component)

Usage:
    python scripts/evaluate_ablation_study.py --dataset data/evaluation_dataset.json --output results/ablation_study.json
"""

import os
import sys
import json
import argparse
import requests
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.evaluate_detection import DetectionEvaluator


class AblationStudyEvaluator:
    """Evaluates FHRI with components removed."""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.results_by_variant = {
            "fhri_full": [],
            "fhri_no_entropy": [],
            "fhri_no_contradiction": [],
            "fhri_no_grounding": [],
            "fhri_no_numeric": [],
            "fhri_no_temporal": []
        }
        
    def test_backend_connection(self) -> bool:
        """Test if backend server is running."""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def compute_fhri_without_component(self, response: Dict[str, Any], 
                                      removed_component: Optional[str] = None) -> Dict[str, Any]:
        """
        Compute FHRI score with a component removed.
        
        This is a post-processing step that recalculates FHRI from subscores.
        """
        meta = response.get("meta", {})
        fhri_subscores = meta.get("fhri_subscores", {})
        fhri = meta.get("fhri")
        
        if not fhri_subscores or fhri is None:
            return {"fhri_ablation": None, "components_used": []}
        
        # Default weights (from fhri_scoring.py)
        default_weights = {
            "grounding": 0.25,
            "numeric": 0.25,
            "temporal": 0.20,
            "citation": 0.15,
            "entropy": 0.15
        }
        
        # Map component names
        component_map = {
            "entropy": "entropy",
            "contradiction": "citation",  # Contradiction uses citation weight
            "grounding": "grounding",
            "numeric": "numeric",
            "temporal": "temporal"
        }
        
        # Get available components (excluding removed one)
        available_components = {}
        for comp_name, subscore_key in component_map.items():
            if comp_name == removed_component:
                continue
            
            # Get normalized subscore
            if comp_name == "entropy":
                # Entropy needs to be normalized (1 - entropy_norm)
                entropy = response.get("entropy")
                if entropy is not None:
                    # Normalize entropy (assuming max entropy ~ 3.0)
                    entropy_norm = min(entropy / 3.0, 1.0)
                    available_components[comp_name] = 1.0 - entropy_norm
            elif comp_name == "contradiction":
                # Contradiction uses citation component
                contradiction = response.get("contradiction_score")
                if contradiction is not None:
                    # Normalize contradiction (1 - contradiction_score)
                    available_components[comp_name] = 1.0 - min(contradiction, 1.0)
            else:
                # Direct subscore
                score = fhri_subscores.get(subscore_key)
                if score is not None:
                    available_components[comp_name] = score
        
        # Recalculate weights (renormalize)
        if not available_components:
            return {"fhri_ablation": None, "components_used": []}
        
        # Get weights for available components
        total_weight = sum(default_weights.get(comp, 0) for comp in available_components.keys())
        
        if total_weight == 0:
            return {"fhri_ablation": None, "components_used": []}
        
        # Compute weighted sum
        fhri_ablation = sum(
            (default_weights.get(comp, 0) / total_weight) * score
            for comp, score in available_components.items()
        )
        
        return {
            "fhri_ablation": round(fhri_ablation, 4),
            "components_used": list(available_components.keys()),
            "component_scores": available_components
        }
    
    def query_chatbot(self, question: str, prev_answer: str = None) -> Dict[str, Any]:
        """Query chatbot with full FHRI enabled."""
        payload = {
            "text": question,
            "k": 5,
            "provider": "auto",
            "use_entropy": True,
            "use_nli": True,
            "use_fhri": True
        }
        
        if prev_answer:
            payload["prev_assistant_turn"] = prev_answer
        
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
    
    def predict_label_with_ablation(self, response: Dict[str, Any], 
                                    variant: str, fhri_threshold: float = 0.65) -> str:
        """Predict label using ablation variant."""
        # Extract scores
        entropy = response.get("entropy")
        contradiction_score = response.get("contradiction_score")
        meta = response.get("meta", {})
        fhri_full = meta.get("fhri")
        
        # Compute ablation FHRI
        removed_component = None
        if variant == "fhri_no_entropy":
            removed_component = "entropy"
        elif variant == "fhri_no_contradiction":
            removed_component = "contradiction"
        elif variant == "fhri_no_grounding":
            removed_component = "grounding"
        elif variant == "fhri_no_numeric":
            removed_component = "numeric"
        elif variant == "fhri_no_temporal":
            removed_component = "temporal"
        
        ablation_result = self.compute_fhri_without_component(response, removed_component)
        fhri_ablation = ablation_result["fhri_ablation"]
        
        # Use full FHRI for fhri_full variant
        if variant == "fhri_full":
            fhri_ablation = fhri_full
        
        # Detection logic (same as DetectionEvaluator)
        # Priority: contradiction > hallucination > accurate
        
        # Contradiction detection (only if not removed)
        if variant != "fhri_no_contradiction" and contradiction_score is not None:
            if contradiction_score >= 0.15:  # Soft threshold
                return "contradiction"
        
        # Hallucination detection
        hallucination_detected = False
        
        # Entropy-based (only if not removed)
        if variant != "fhri_no_entropy" and entropy is not None:
            if entropy > 2.0:
                hallucination_detected = True
        
        # FHRI-based (using ablation score)
        if fhri_ablation is not None:
            # High-risk floor breach
            fhri_subscores = meta.get("fhri_subscores", {})
            scenario_detected = meta.get("scenario_detected", "default")
            
            # Check high-risk floor (0.85) for numeric questions
            if scenario_detected in ["numeric_kpi", "intraday"]:
                if fhri_ablation < 0.85:
                    hallucination_detected = True
            
            # Check scenario threshold
            from src.fhri_scoring import SCENARIO_FHRI_THRESHOLDS
            scenario_key = scenario_detected.lower() if scenario_detected else "default"
            threshold = SCENARIO_FHRI_THRESHOLDS.get(scenario_key, fhri_threshold)
            
            if fhri_ablation <= threshold:
                hallucination_detected = True
        
        if hallucination_detected:
            return "hallucination"
        
        # Accurate (FHRI above threshold)
        if fhri_ablation is not None and fhri_ablation > fhri_threshold:
            return "accurate"
        
        # Fallback
        return "accurate"
    
    def evaluate_sample(self, sample: Dict[str, Any], prev_answer: str = None) -> Dict[str, Any]:
        """Evaluate a single sample with all ablation variants."""
        sample_id = sample.get("id", "unknown")
        question = sample.get("question", "")
        true_label = sample.get("ground_truth_label", sample.get("your_annotation", ""))
        
        if not true_label or true_label not in ["accurate", "hallucination", "contradiction"]:
            return None
        
        # Query once (with full FHRI)
        response = self.query_chatbot(question, prev_answer)
        if not response:
            return None
        
        results = {
            "sample_id": sample_id,
            "question": question,
            "true_label": true_label
        }
        
        # Evaluate each variant
        variants = [
            "fhri_full",
            "fhri_no_entropy",
            "fhri_no_contradiction",
            "fhri_no_grounding",
            "fhri_no_numeric",
            "fhri_no_temporal"
        ]
        
        for variant in variants:
            predicted_label = self.predict_label_with_ablation(response, variant)
            
            # Get ablation FHRI
            removed = None
            if variant != "fhri_full":
                removed = variant.replace("fhri_no_", "")
            ablation_result = self.compute_fhri_without_component(response, removed)
            
            result_entry = {
                "predicted_label": predicted_label,
                "correct": predicted_label == true_label,
                "fhri_ablation": ablation_result["fhri_ablation"],
                "components_used": ablation_result["components_used"]
            }
            
            results[variant] = result_entry
            
            self.results_by_variant[variant].append({
                "sample_id": sample_id,
                "true_label": true_label,
                "predicted_label": predicted_label,
                "correct": predicted_label == true_label,
                **result_entry
            })
        
        return results
    
    def evaluate_dataset(self, dataset_path: str) -> Dict[str, Any]:
        """Evaluate entire dataset with all ablation variants."""
        print("=" * 70)
        print("ABLATION STUDY EVALUATION")
        print("=" * 70)
        print(f"Dataset: {dataset_path}")
        print(f"Backend: {self.backend_url}")
        print("Variants: Full, -Entropy, -Contradiction, -Grounding, -Numeric, -Temporal")
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
                response = self.query_chatbot(sample.get("question", ""), prev_answer)
                if response and response.get("answer"):
                    if pair_id not in pair_data:
                        pair_data[pair_id] = []
                    pair_data[pair_id].append((
                        sample.get("id", ""),
                        sample.get("question", ""),
                        response.get("answer", ""),
                        sample.get("ground_truth_label", "")
                    ))
            
            time.sleep(0.3)  # Rate limiting
        
        return self.calculate_ablation_metrics()
    
    def calculate_ablation_metrics(self) -> Dict[str, Any]:
        """Calculate metrics for each ablation variant."""
        metrics = {}
        
        for variant, results in self.results_by_variant.items():
            if not results:
                continue
            
            classes = ["hallucination", "accurate", "contradiction"]
            variant_metrics = {}
            
            for cls in classes:
                tp = sum(1 for r in results if r["true_label"] == cls and r["predicted_label"] == cls)
                fp = sum(1 for r in results if r["true_label"] != cls and r["predicted_label"] == cls)
                fn = sum(1 for r in results if r["true_label"] == cls and r["predicted_label"] != cls)
                
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
                
                variant_metrics[cls] = {
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
            macro_f1 = sum(m["f1_score"] for m in variant_metrics.values()) / len(variant_metrics) if variant_metrics else 0.0
            
            metrics[variant] = {
                "overall": {
                    "accuracy": round(overall_accuracy, 4),
                    "macro_f1": round(macro_f1, 4),
                    "total_samples": len(results),
                    "correct_predictions": correct
                },
                "per_class": variant_metrics
            }
        
        return metrics
    
    def print_ablation_report(self, metrics: Dict[str, Any]):
        """Print ablation study report."""
        print("\n" + "=" * 70)
        print("ABLATION STUDY RESULTS")
        print("=" * 70)
        
        variants = [
            "fhri_full",
            "fhri_no_entropy",
            "fhri_no_contradiction",
            "fhri_no_grounding",
            "fhri_no_numeric",
            "fhri_no_temporal"
        ]
        
        variant_names = {
            "fhri_full": "FHRI-Full",
            "fhri_no_entropy": "FHRI - Entropy",
            "fhri_no_contradiction": "FHRI - Contradiction",
            "fhri_no_grounding": "FHRI - Grounding",
            "fhri_no_numeric": "FHRI - Numeric",
            "fhri_no_temporal": "FHRI - Temporal"
        }
        
        # Overall comparison
        print("\n📊 Overall Performance (Component Removal Impact):")
        print(f"\n{'Variant':<25} {'Accuracy':<12} {'Macro F1':<12} {'Δ F1 vs Full':<15}")
        print("-" * 70)
        
        baseline_f1 = metrics.get("fhri_full", {}).get("overall", {}).get("macro_f1", 0.0)
        
        for variant in variants:
            if variant in metrics:
                m = metrics[variant]["overall"]
                delta_f1 = m["macro_f1"] - baseline_f1
                delta_str = f"{delta_f1:+.4f}" if variant != "fhri_full" else "baseline"
                print(f"{variant_names[variant]:<25} {m['accuracy']:<12.4f} {m['macro_f1']:<12.4f} {delta_str:<15}")
        
        # Component contribution analysis
        print("\n📋 Component Contribution Analysis:")
        print("(Negative Δ F1 = component is important, Positive = component may hurt)")
        print(f"\n{'Removed Component':<25} {'Macro F1':<12} {'Δ vs Full':<15} {'Impact':<20}")
        print("-" * 70)
        
        for variant in variants:
            if variant == "fhri_full":
                continue
            
            if variant in metrics:
                m = metrics[variant]["overall"]
                delta_f1 = m["macro_f1"] - baseline_f1
                component = variant.replace("fhri_no_", "").title()
                
                if delta_f1 < -0.05:
                    impact = "High (critical)"
                elif delta_f1 < -0.02:
                    impact = "Medium (important)"
                elif delta_f1 < 0.02:
                    impact = "Low (minor)"
                else:
                    impact = "Negative (harmful)"
                
                print(f"{component:<25} {m['macro_f1']:<12.4f} {delta_f1:+.4f}{'':<10} {impact:<20}")
        
        print("\n" + "=" * 70)
    
    def save_report(self, output_path: str, metrics: Dict[str, Any]):
        """Save ablation report to JSON."""
        report = {
            "evaluation_metadata": {
                "backend_url": self.backend_url,
                "evaluation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "variants": list(self.results_by_variant.keys())
            },
            "metrics": metrics,
            "detailed_results": self.results_by_variant
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n[OK] Report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate ablation study")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/evaluation_dataset.json",
        help="Path to evaluation dataset"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/ablation_study.json",
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
    
    evaluator = AblationStudyEvaluator(backend_url=args.backend)
    metrics = evaluator.evaluate_dataset(args.dataset)
    
    if metrics:
        evaluator.print_ablation_report(metrics)
        evaluator.save_report(args.output, metrics)
        print("\n[OK] Ablation study complete!")
    else:
        print("\n[ERROR] Evaluation failed")


if __name__ == "__main__":
    main()




















