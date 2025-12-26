"""
Test script to verify contradiction detection fix.
Focuses only on contradiction samples to check if NLI scores are now present.
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import the evaluator
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))
from evaluate_detection import DetectionEvaluator

def test_contradiction_pairs():
    """Test contradiction detection with focus on missing NLI scores."""
    
    print("=" * 80)
    print("TESTING CONTRADICTION DETECTION FIX")
    print("=" * 80)
    
    # Load dataset
    dataset_path = "data/evaluation_dataset.json"
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    samples = dataset.get("samples", [])
    
    # Filter only contradiction samples
    contradiction_samples = [s for s in samples if s.get("ground_truth_label") == "contradiction"]
    
    print(f"\nFound {len(contradiction_samples)} contradiction samples in dataset")
    print("=" * 80)
    
    # Group by contradiction_pair_id to test pair tracking
    pair_groups = {}
    for sample in contradiction_samples:
        pair_id = sample.get("fhri_spec", {}).get("contradiction_pair_id")
        if pair_id:
            if pair_id not in pair_groups:
                pair_groups[pair_id] = []
            pair_groups[pair_id].append(sample)
    
    print(f"\nContradiction pairs found: {len(pair_groups)}")
    for pair_id, samples_in_pair in pair_groups.items():
        print(f"  {pair_id}: {len(samples_in_pair)} samples")
        for s in samples_in_pair:
            print(f"    - {s.get('id')}: {s.get('question', '')[:60]}...")
    
    # Initialize evaluator
    evaluator = DetectionEvaluator(
        backend_url="http://localhost:8000",
        hallu_threshold=2.0,
        fhri_threshold=0.65
    )
    
    # Test backend connection
    if not evaluator.test_backend_connection():
        print("\n❌ Backend not running! Please start the server first.")
        return
    
    print("\n" + "=" * 80)
    print("TESTING CONTRADICTION PAIRS WITH FIXED LOGIC")
    print("=" * 80)
    
    # Test the pair tracking logic
    pair_answers = {}  # Maps contradiction_pair_id -> list of (sample_id, answer, true_label) tuples
    
    results = []
    
    # Process all samples (not just contradictions) to get previous answers
    all_samples = dataset.get("samples", [])
    
    for i, sample in enumerate(all_samples, 1):
        fhri_spec = sample.get("fhri_spec", {})
        pair_id = fhri_spec.get("contradiction_pair_id")
        sample_id = sample.get("id", "")
        true_label = sample.get("ground_truth_label", "")
        
        # Only test if this is a contradiction sample
        if true_label != "contradiction":
            # Still need to process to store answers for pairs
            if pair_id:
                prev_answer = None
                if pair_id in pair_answers:
                    stored_pairs = pair_answers[pair_id]
                    if true_label == "contradiction":
                        for stored_sample_id, stored_answer, stored_label in reversed(stored_pairs):
                            if stored_sample_id != sample_id and stored_answer and stored_label == "accurate":
                                prev_answer = stored_answer
                                break
                        if not prev_answer:
                            for stored_sample_id, stored_answer, stored_label in reversed(stored_pairs):
                                if stored_sample_id != sample_id and stored_answer:
                                    prev_answer = stored_answer
                                    break
                
                result = evaluator.evaluate_sample(sample, prev_answer=prev_answer)
                if result and pair_id:
                    llm_answer = result.get("llm_answer", "")
                    # Only store if we got a valid answer (not empty)
                    if llm_answer and llm_answer.strip():
                        if pair_id not in pair_answers:
                            pair_answers[pair_id] = []
                        pair_answers[pair_id].append((sample_id, llm_answer, true_label))
                        print(f"  ✓ Stored answer for {sample_id} (length: {len(llm_answer)})")
                    else:
                        print(f"  ⚠️  {sample_id} returned empty answer, not storing for pairs")
                elif not result:
                    print(f"  ❌ {sample_id} evaluation failed - no result returned")
            continue
        
        # This is a contradiction sample - test it
        print(f"\n[{i}/{len(all_samples)}] Testing {sample_id} (contradiction)")
        print(f"  Question: {sample.get('question', '')[:70]}...")
        
        # Get previous answer using fixed logic
        prev_answer = None
        if pair_id:
            if pair_id in pair_answers:
                stored_pairs = pair_answers[pair_id]
                # Find the most recent "accurate" answer
                for stored_sample_id, stored_answer, stored_label in reversed(stored_pairs):
                    if stored_sample_id != sample_id and stored_answer and stored_label == "accurate":
                        prev_answer = stored_answer
                        print(f"  ✓ Found previous answer from {stored_sample_id} (accurate)")
                        break
                # Fallback if no accurate answer
                if not prev_answer:
                    for stored_sample_id, stored_answer, stored_label in reversed(stored_pairs):
                        if stored_sample_id != sample_id and stored_answer:
                            prev_answer = stored_answer
                            print(f"  ⚠️  Using fallback answer from {stored_sample_id}")
                            break
            else:
                print(f"  ⚠️  No previous answers found for pair {pair_id}")
        
        # Evaluate the sample
        result = evaluator.evaluate_sample(sample, prev_answer=prev_answer)
        
        if result:
            nli_score = result.get("contradiction_score")
            predicted = result.get("predicted_label")
            correct = result.get("correct")
            
            print(f"  Result:")
            nli_str = f"{nli_score:.3f}" if nli_score is not None else "❌ MISSING"
            print(f"    • NLI Score: {nli_str}")
            print(f"    • Predicted: {predicted}")
            print(f"    • Correct: {'✓' if correct else '✗'}")
            
            if nli_score is None:
                print(f"    ⚠️  ISSUE: NLI score is missing!")
            elif nli_score > 0.15:
                print(f"    ✓ NLI above threshold (0.15) - should be detected")
            else:
                gap = 0.15 - nli_score
                print(f"    ⚠️  NLI below threshold (gap: {gap:.3f})")
            
            results.append({
                "sample_id": sample_id,
                "pair_id": pair_id,
                "has_prev_answer": prev_answer is not None,
                "nli_score": nli_score,
                "predicted": predicted,
                "correct": correct
            })
            
            # Store answer for future pairs (only if valid)
            if pair_id:
                llm_answer = result.get("llm_answer", "")
                if llm_answer and llm_answer.strip():
                    if pair_id not in pair_answers:
                        pair_answers[pair_id] = []
                    pair_answers[pair_id].append((sample_id, llm_answer, true_label))
                else:
                    print(f"  ⚠️  {sample_id} returned empty answer, not storing for pairs")
        
        import time
        time.sleep(0.5)  # Avoid overwhelming server
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total = len(results)
    with_nli = sum(1 for r in results if r["nli_score"] is not None)
    without_nli = total - with_nli
    correct = sum(1 for r in results if r["correct"])
    detected = sum(1 for r in results if r["predicted"] == "contradiction")
    
    print(f"\nTotal contradiction samples tested: {total}")
    print(f"  • With NLI scores: {with_nli} ({with_nli/total*100:.1f}%)")
    print(f"  • Without NLI scores: {without_nli} ({without_nli/total*100:.1f}%)")
    print(f"  • Correctly predicted: {correct} ({correct/total*100:.1f}%)")
    print(f"  • Detected as contradiction: {detected} ({detected/total*100:.1f}%)")
    
    if without_nli > 0:
        print(f"\n❌ ISSUE: {without_nli} samples still missing NLI scores:")
        for r in results:
            if r["nli_score"] is None:
                print(f"    • {r['sample_id']}: has_prev_answer={r['has_prev_answer']}")
    else:
        print(f"\n✅ SUCCESS: All contradiction samples now have NLI scores!")
    
    # Check which ones were detected
    print(f"\nDetection breakdown:")
    for r in results:
        status = "✓" if r["correct"] else "✗"
        nli_str = f"{r['nli_score']:.3f}" if r["nli_score"] is not None else "MISSING"
        print(f"  {status} {r['sample_id']}: NLI={nli_str}, Predicted={r['predicted']}, HasPrev={r['has_prev_answer']}")
    
    # Save results
    output_file = "results/test_contradiction_fix.json"
    os.makedirs("results", exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_summary": {
                "total_samples": total,
                "with_nli": with_nli,
                "without_nli": without_nli,
                "correct": correct,
                "detected": detected
            },
            "detailed_results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Results saved to {output_file}")
    print("=" * 80)

if __name__ == "__main__":
    test_contradiction_pairs()

