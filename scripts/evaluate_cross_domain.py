"""
Cross-Domain Comparison Evaluation Script

This script compares FHRI performance across different domains:
1. Finance QA dataset (domain-specific)
2. General QA dataset (open-domain)

Usage:
    python scripts/evaluate_cross_domain.py \
        --finance_dataset data/evaluation_dataset.json \
        --general_dataset data/general_qa_dataset.json \
        --output results/cross_domain_comparison.json
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


class CrossDomainEvaluator:
    """Evaluates FHRI performance across different domains."""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.results_by_domain = {
            "finance": [],
            "general": []
        }
        
    def test_backend_connection(self) -> bool:
        """Test if backend server is running."""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
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
    
    def evaluate_sample(self, sample: Dict[str, Any], domain: str, 
                        prev_answer: str = None) -> Dict[str, Any]:
        """Evaluate a single sample."""
        sample_id = sample.get("id", "unknown")
        question = sample.get("question", "")
        true_label = sample.get("ground_truth_label", sample.get("your_annotation", ""))
        
        if not true_label or true_label not in ["accurate", "hallucination", "contradiction"]:
            return None
        
        # Query chatbot
        response = self.query_chatbot(question, prev_answer)
        if not response:
            return None
        
        # Extract scores
        entropy = response.get("entropy")
        contradiction_score = response.get("contradiction_score")
        meta = response.get("meta", {})
        fhri = meta.get("fhri")
        fhri_subscores = meta.get("fhri_subscores", {})
        scenario_detected = meta.get("scenario_detected", "default")
        
        # Predict label (using DetectionEvaluator logic)
        from src.fhri_scoring import SCENARIO_FHRI_THRESHOLDS, evaluate_fhri_risk
        
        scenario_key = (scenario_detected or "default").lower()
        scenario_threshold = SCENARIO_FHRI_THRESHOLDS.get(scenario_key, 0.65)
        
        # Contradiction detection
        contradiction_detected = False
        if contradiction_score is not None:
            if contradiction_score >= 0.15:  # Soft threshold
                contradiction_detected = True
        
        # Hallucination detection
        hallucination_detected = False
        if entropy is not None and entropy > 2.0:
            hallucination_detected = True
        
        # FHRI risk evaluation
        if fhri is not None:
            risk_metadata = evaluate_fhri_risk(fhri, scenario_key, question, scenario_threshold)
            if risk_metadata and risk_metadata.get("high_risk_floor_breach"):
                hallucination_detected = True
            if fhri <= scenario_threshold:
                hallucination_detected = True
        
        # Predict label
        if contradiction_detected:
            predicted_label = "contradiction"
        elif hallucination_detected:
            predicted_label = "hallucination"
        elif fhri is not None and fhri > scenario_threshold:
            predicted_label = "accurate"
        else:
            predicted_label = "accurate"  # Fallback
        
        result = {
            "sample_id": sample_id,
            "question": question,
            "true_label": true_label,
            "predicted_label": predicted_label,
            "correct": predicted_label == true_label,
            "entropy": entropy,
            "contradiction_score": contradiction_score,
            "fhri": fhri,
            "fhri_subscores": fhri_subscores,
            "scenario_detected": scenario_detected,
            "domain": domain
        }
        
        self.results_by_domain[domain].append(result)
        return result
    
    def evaluate_dataset(self, dataset_path: str, domain: str) -> List[Dict[str, Any]]:
        """Evaluate a dataset for a specific domain."""
        print(f"\n{'='*70}")
        print(f"Evaluating {domain.upper()} Domain Dataset")
        print(f"{'='*70}")
        print(f"Dataset: {dataset_path}")
        
        if not self.test_backend_connection():
            print("\n[ERROR] Backend server is not running")
            return []
        
        # Load dataset
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
        except Exception as e:
            print(f"[ERROR] Error loading dataset: {e}")
            return []
        
        samples = dataset.get("samples", [])
        print(f"Found {len(samples)} samples")
        print("=" * 70)
        
        # Track contradiction pairs
        pair_data = {}
        results = []
        
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
            
            result = self.evaluate_sample(sample, domain, prev_answer)
            
            if result:
                results.append(result)
                status = "[OK]" if result["correct"] else "[X]"
                print(f"  {status} True={result['true_label']}, Predicted={result['predicted_label']}")
                
                # Store answer for pairs
                if pair_id:
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
        
        return results
    
    def calculate_domain_metrics(self, domain: str) -> Dict[str, Any]:
        """Calculate metrics for a specific domain."""
        results = self.results_by_domain.get(domain, [])
        if not results:
            return {}
        
        classes = ["hallucination", "accurate", "contradiction"]
        metrics = {}
        
        for cls in classes:
            tp = sum(1 for r in results if r["true_label"] == cls and r["predicted_label"] == cls)
            fp = sum(1 for r in results if r["true_label"] != cls and r["predicted_label"] == cls)
            fn = sum(1 for r in results if r["true_label"] == cls and r["predicted_label"] != cls)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            metrics[cls] = {
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
        macro_f1 = sum(m["f1_score"] for m in metrics.values()) / len(metrics) if metrics else 0.0
        
        # Component analysis
        avg_fhri = sum(r["fhri"] for r in results if r["fhri"] is not None) / len([r for r in results if r["fhri"] is not None]) if results else 0.0
        avg_entropy = sum(r["entropy"] for r in results if r["entropy"] is not None) / len([r for r in results if r["entropy"] is not None]) if results else 0.0
        
        return {
            "overall": {
                "accuracy": round(overall_accuracy, 4),
                "macro_f1": round(macro_f1, 4),
                "total_samples": len(results),
                "correct_predictions": correct,
                "avg_fhri": round(avg_fhri, 4),
                "avg_entropy": round(avg_entropy, 4)
            },
            "per_class": metrics
        }
    
    def print_cross_domain_report(self, metrics: Dict[str, Dict[str, Any]]):
        """Print cross-domain comparison report."""
        print("\n" + "=" * 70)
        print("CROSS-DOMAIN COMPARISON RESULTS")
        print("=" * 70)
        
        # Overall comparison
        print("\n📊 Overall Performance by Domain:")
        print(f"\n{'Domain':<20} {'Accuracy':<12} {'Macro F1':<12} {'Avg FHRI':<12} {'Samples':<10}")
        print("-" * 70)
        
        for domain in ["finance", "general"]:
            if domain in metrics:
                m = metrics[domain]["overall"]
                print(f"{domain.capitalize():<20} {m['accuracy']:<12.4f} {m['macro_f1']:<12.4f} {m['avg_fhri']:<12.4f} {m['total_samples']:<10}")
        
        # Per-class comparison
        print("\n📋 Per-Class F1-Score by Domain:")
        classes = ["hallucination", "accurate", "contradiction"]
        print(f"\n{'Class':<20} {'Finance F1':<15} {'General F1':<15} {'Difference':<15}")
        print("-" * 70)
        
        for cls in classes:
            finance_f1 = metrics.get("finance", {}).get("per_class", {}).get(cls, {}).get("f1_score", 0.0)
            general_f1 = metrics.get("general", {}).get("per_class", {}).get(cls, {}).get("f1_score", 0.0)
            diff = finance_f1 - general_f1
            print(f"{cls.capitalize():<20} {finance_f1:<15.4f} {general_f1:<15.4f} {diff:+.4f}{'':<10}")
        
        # Domain adaptation analysis
        print("\n🔍 Domain Adaptation Analysis:")
        if "finance" in metrics and "general" in metrics:
            finance_f1 = metrics["finance"]["overall"]["macro_f1"]
            general_f1 = metrics["general"]["overall"]["macro_f1"]
            improvement = finance_f1 - general_f1
            
            if improvement > 0.05:
                conclusion = "Strong domain adaptation (FHRI performs significantly better in finance)"
            elif improvement > 0.02:
                conclusion = "Moderate domain adaptation (FHRI performs better in finance)"
            elif improvement > -0.02:
                conclusion = "Neutral (FHRI performs similarly across domains)"
            else:
                conclusion = "Negative adaptation (FHRI performs worse in finance - may need tuning)"
            
            print(f"  Finance Macro F1: {finance_f1:.4f}")
            print(f"  General Macro F1: {general_f1:.4f}")
            print(f"  Difference: {improvement:+.4f}")
            print(f"  Conclusion: {conclusion}")
        
        print("\n" + "=" * 70)
    
    def save_report(self, output_path: str, metrics: Dict[str, Dict[str, Any]]):
        """Save cross-domain report to JSON."""
        report = {
            "evaluation_metadata": {
                "backend_url": self.backend_url,
                "evaluation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "domains": ["finance", "general"]
            },
            "metrics": metrics,
            "detailed_results": self.results_by_domain
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n[OK] Report saved to: {output_path}")


def create_general_qa_template(output_path: str):
    """Create a template for general QA dataset."""
    template = {
        "metadata": {
            "dataset_name": "General QA Evaluation Dataset",
            "version": "1.0",
            "description": "Open-domain QA samples for cross-domain comparison",
            "annotation_date": time.strftime("%Y-%m-%d"),
            "total_samples": 0
        },
        "annotation_guidelines": {
            "accurate": "Answer is factually correct and grounded",
            "hallucination": "Answer contains fabricated or incorrect information",
            "contradiction": "Answer contradicts a previous response"
        },
        "samples": [
            {
                "id": "general_001",
                "question": "What is the capital of France?",
                "ground_truth_label": "accurate",
                "your_annotation": "accurate"
            },
            {
                "id": "general_002",
                "question": "Who wrote Romeo and Juliet?",
                "ground_truth_label": "accurate",
                "your_annotation": "accurate"
            }
        ]
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Template created at: {output_path}")
    print("Please add your general QA samples to this file.")


def main():
    parser = argparse.ArgumentParser(description="Evaluate cross-domain comparison")
    parser.add_argument(
        "--finance_dataset",
        type=str,
        default="data/evaluation_dataset.json",
        help="Path to finance QA dataset"
    )
    parser.add_argument(
        "--general_dataset",
        type=str,
        default="data/general_qa_dataset.json",
        help="Path to general QA dataset"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/cross_domain_comparison.json",
        help="Path to save report"
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="http://localhost:8000",
        help="Backend server URL"
    )
    parser.add_argument(
        "--create_template",
        action="store_true",
        help="Create a template for general QA dataset"
    )
    
    args = parser.parse_args()
    
    if args.create_template:
        create_general_qa_template(args.general_dataset)
        return
    
    evaluator = CrossDomainEvaluator(backend_url=args.backend)
    
    # Evaluate finance domain
    if os.path.exists(args.finance_dataset):
        evaluator.evaluate_dataset(args.finance_dataset, "finance")
    else:
        print(f"[WARN] Finance dataset not found: {args.finance_dataset}")
    
    # Evaluate general domain
    if os.path.exists(args.general_dataset):
        evaluator.evaluate_dataset(args.general_dataset, "general")
    else:
        print(f"[WARN] General dataset not found: {args.general_dataset}")
        print(f"      Run with --create_template to create a template")
        return
    
    # Calculate metrics
    metrics = {
        "finance": evaluator.calculate_domain_metrics("finance"),
        "general": evaluator.calculate_domain_metrics("general")
    }
    
    if metrics["finance"] and metrics["general"]:
        evaluator.print_cross_domain_report(metrics)
        evaluator.save_report(args.output, metrics)
        print("\n[OK] Cross-domain evaluation complete!")
    else:
        print("\n[ERROR] Evaluation failed or incomplete")


if __name__ == "__main__":
    main()




















