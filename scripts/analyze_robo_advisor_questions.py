"""
Analyze robo-advisor/portfolio advice questions and their prediction accuracy.

Identifies questions related to portfolio allocation, diversification, and investment advice,
then checks if they're being incorrectly flagged as hallucinations.
"""

import json
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def is_robo_advisor_question(question: str, category: str, scenario: str) -> bool:
    """Check if question is robo-advisor/portfolio advice related."""
    robo_keywords = [
        "allocation", "portfolio", "diversif", "80%", "20%", "60%", "40%",
        "equity", "bond", "ETF", "retire", "risk tolerance", "aggressive",
        "conservative", "asset mix", "investment horizon", "suitability"
    ]
    
    question_lower = question.lower()
    is_robo = (
        category == "investment_advice" or
        "portfolio advice" in scenario.lower() or
        "suitability" in scenario.lower() or
        any(keyword in question_lower for keyword in robo_keywords)
    )
    
    return is_robo


def analyze_robo_advisor_questions(dataset_path: str, results_path: str):
    """Analyze robo-advisor questions and their prediction accuracy."""
    
    # Load dataset
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    # Load results
    with open(results_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Create mapping: sample_id -> result
    results_map = {}
    for result in results.get("detailed_results", []):
        results_map[result["sample_id"]] = result
    
    # Analyze robo-advisor questions
    robo_questions = []
    stock_questions = []
    
    samples = dataset.get("samples", [])
    
    for sample in samples:
        sample_id = sample.get("id", "")
        question = sample.get("question", "")
        fhri_spec = sample.get("fhri_spec", {})
        category = fhri_spec.get("category", "")
        scenario = fhri_spec.get("expected_scenario", "")
        true_label = sample.get("ground_truth_label", "")
        
        # Check if robo-advisor question
        if is_robo_advisor_question(question, category, scenario):
            result = results_map.get(sample_id)
            if result:
                robo_questions.append({
                    "id": sample_id,
                    "question": question,
                    "category": category,
                    "scenario": scenario,
                    "true_label": true_label,
                    "predicted_label": result.get("predicted_label", ""),
                    "correct": result.get("correct", False),
                    "fhri": result.get("fhri"),
                    "scenario_detected": result.get("scenario_detected", ""),
                    "fhri_threshold_used": result.get("fhri_threshold_used")
                })
        else:
            # Check if stock-related (not robo-advisor)
            stock_keywords = ["stock", "ticker", "price", "earnings", "eps", "revenue", 
                            "dividend", "pe ratio", "market cap", "trading", "buy", "sell"]
            question_lower = question.lower()
            if any(keyword in question_lower for keyword in stock_keywords):
                result = results_map.get(sample_id)
                if result:
                    stock_questions.append({
                        "id": sample_id,
                        "question": question,
                        "category": category,
                        "scenario": scenario,
                        "true_label": true_label,
                        "predicted_label": result.get("predicted_label", ""),
                        "correct": result.get("correct", False),
                        "fhri": result.get("fhri"),
                        "scenario_detected": result.get("scenario_detected", ""),
                        "fhri_threshold_used": result.get("fhri_threshold_used")
                    })
    
    # Calculate statistics
    robo_total = len(robo_questions)
    robo_correct = sum(1 for q in robo_questions if q["correct"])
    robo_incorrect = robo_total - robo_correct
    robo_accuracy = (robo_correct / robo_total * 100) if robo_total > 0 else 0
    
    # False predictions (should be accurate but predicted as hallucination)
    robo_false_negatives = [
        q for q in robo_questions 
        if q["true_label"] == "accurate" and q["predicted_label"] == "hallucination"
    ]
    
    stock_total = len(stock_questions)
    stock_correct = sum(1 for q in stock_questions if q["correct"])
    stock_incorrect = stock_total - stock_correct
    stock_accuracy = (stock_correct / stock_total * 100) if stock_total > 0 else 0
    
    stock_false_negatives = [
        q for q in stock_questions 
        if q["true_label"] == "accurate" and q["predicted_label"] == "hallucination"
    ]
    
    # Print results
    print("=" * 80)
    print("ROBO-ADVISOR / PORTFOLIO ADVICE QUESTIONS ANALYSIS")
    print("=" * 80)
    print(f"\nTotal Robo-Advisor Questions: {robo_total}")
    print(f"Correct Predictions: {robo_correct} ({robo_accuracy:.1f}%)")
    print(f"Incorrect Predictions: {robo_incorrect} ({100-robo_accuracy:.1f}%)")
    print(f"\nFalse Negatives (Accurate -> Hallucination): {len(robo_false_negatives)}")
    
    if robo_false_negatives:
        print("\n" + "-" * 80)
        print("FALSE NEGATIVES (Robo-Advisor Questions Flagged as Hallucination):")
        print("-" * 80)
        for q in robo_false_negatives:
            print(f"\n[{q['id']}] {q['question'][:70]}...")
            print(f"  True Label: {q['true_label']} | Predicted: {q['predicted_label']}")
            print(f"  FHRI: {q['fhri']:.3f} | Threshold: {q['fhri_threshold_used']}")
            print(f"  Scenario: {q['scenario']} -> Detected: {q['scenario_detected']}")
    
    print("\n" + "=" * 80)
    print("STOCK-RELATED QUESTIONS ANALYSIS (for comparison)")
    print("=" * 80)
    print(f"\nTotal Stock Questions: {stock_total}")
    print(f"Correct Predictions: {stock_correct} ({stock_accuracy:.1f}%)")
    print(f"Incorrect Predictions: {stock_incorrect} ({100-stock_accuracy:.1f}%)")
    print(f"\nFalse Negatives (Accurate -> Hallucination): {len(stock_false_negatives)}")
    
    if stock_false_negatives:
        print("\n" + "-" * 80)
        print("FALSE NEGATIVES (Stock Questions Flagged as Hallucination):")
        print("-" * 80)
        for q in stock_false_negatives[:5]:  # Show first 5
            print(f"\n[{q['id']}] {q['question'][:70]}...")
            print(f"  True Label: {q['true_label']} | Predicted: {q['predicted_label']}")
            print(f"  FHRI: {q['fhri']:.3f} | Threshold: {q['fhri_threshold_used']}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Robo-Advisor Questions: {robo_total} ({robo_accuracy:.1f}% accuracy)")
    print(f"Stock Questions: {stock_total} ({stock_accuracy:.1f}% accuracy)")
    
    if robo_accuracy < stock_accuracy:
        print(f"\n[WARNING] Robo-advisor questions have LOWER accuracy than stock questions!")
        print(f"   Difference: {stock_accuracy - robo_accuracy:.1f}%")
        print(f"   This suggests robo-advisor questions may not be appropriate for your stock-focused dataset.")
    else:
        print(f"\n[OK] Robo-advisor questions have similar or better accuracy than stock questions.")
    
    return {
        "robo_total": robo_total,
        "robo_correct": robo_correct,
        "robo_accuracy": robo_accuracy,
        "robo_false_negatives": len(robo_false_negatives),
        "stock_total": stock_total,
        "stock_correct": stock_correct,
        "stock_accuracy": stock_accuracy,
        "stock_false_negatives": len(stock_false_negatives),
        "robo_false_negative_details": robo_false_negatives
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze robo-advisor questions")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/evaluation_dataset.json",
        help="Path to evaluation dataset"
    )
    parser.add_argument(
        "--results",
        type=str,
        default="results/test_0.70_scenario.json",
        help="Path to evaluation results"
    )
    
    args = parser.parse_args()
    
    analyze_robo_advisor_questions(args.dataset, args.results)

