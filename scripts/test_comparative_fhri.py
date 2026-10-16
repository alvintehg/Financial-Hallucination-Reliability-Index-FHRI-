"""
Test script for comparative query FHRI handling.

Tests the enhanced FHRI and contradiction calibration logic for:
1. Comparative intent detection
2. Directional contrast detection
3. Semantic similarity pre-check
4. FHRI recalibration for grounded but divergent answers
5. Label smoothing and tier mapping
6. Contradiction normalization with EMA smoothing
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scenario_detection import detect_comparative_intent, detect_scenario
from nli_infer import (
    load_model,
    contradiction_score,
    contradiction_score_comparative,
    detect_directional_contrast
)
from adaptive_fhri import AdaptiveFHRIScorer, compute_semantic_similarity


def test_comparative_intent_detection():
    """Test comparative intent detection."""
    print("\n" + "="*80)
    print("TEST 1: Comparative Intent Detection")
    print("="*80)

    test_queries = [
        ("Compare CRWV vs NBIS", True),
        ("Which is better, AAPL or MSFT?", True),
        ("What is AAPL's P/E ratio?", False),
        ("TSLA vs RIVN performance", True),
        ("How did the market perform today?", False),
        ("Compare the fundamentals of Amazon and Google", True),
    ]

    for query, expected in test_queries:
        detected = detect_comparative_intent(query)
        status = "✓" if detected == expected else "✗"
        print(f"{status} Query: {query}")
        print(f"   Expected: {expected}, Detected: {detected}")


def test_directional_contrast():
    """Test directional contrast detection."""
    print("\n" + "="*80)
    print("TEST 2: Directional Contrast Detection")
    print("="*80)

    test_cases = [
        ("AAPL is up 5%", "MSFT is down 2%", True),
        ("Stock A is rising", "Stock B is falling", True),
        ("TSLA gained 10%", "RIVN lost 8%", True),
        ("Both stocks are up", "Both stocks are up", False),
        ("Price increased", "Volume decreased", False),
    ]

    for text1, text2, expected in test_cases:
        detected = detect_directional_contrast(text1, text2)
        status = "✓" if detected == expected else "✗"
        print(f"{status} Text1: {text1}")
        print(f"   Text2: {text2}")
        print(f"   Expected: {expected}, Detected: {detected}")


def test_contradiction_score_comparative():
    """Test comparative contradiction scoring with NLI model."""
    print("\n" + "="*80)
    print("TEST 3: Comparative Contradiction Scoring")
    print("="*80)

    try:
        tokenizer, model = load_model()

        test_cases = [
            {
                "premise": "Apple stock is up 3% today",
                "hypothesis": "Microsoft stock is down 2% today",
                "query": "Compare AAPL vs MSFT performance",
                "comparative_intent": True,
                "expected_reduction": True
            },
            {
                "premise": "Apple's P/E ratio is 25",
                "hypothesis": "Apple's P/E ratio is 30",
                "query": "What is Apple's P/E?",
                "comparative_intent": False,
                "expected_reduction": False
            },
            {
                "premise": "CRWV is outperforming",
                "hypothesis": "NBIS is underperforming",
                "query": "Compare CRWV vs NBIS",
                "comparative_intent": True,
                "expected_reduction": True
            }
        ]

        for i, case in enumerate(test_cases):
            print(f"\nTest Case {i+1}:")
            print(f"  Premise: {case['premise']}")
            print(f"  Hypothesis: {case['hypothesis']}")
            print(f"  Query: {case['query']}")

            # Raw contradiction score
            raw_score, raw_probs = contradiction_score(
                case['premise'], case['hypothesis'], tokenizer, model
            )

            # Comparative-aware score
            adjusted_score, adj_probs, metadata = contradiction_score_comparative(
                case['premise'],
                case['hypothesis'],
                tokenizer,
                model,
                query=case['query'],
                comparative_intent=case['comparative_intent']
            )

            print(f"  Raw contradiction: {raw_score:.3f}")
            print(f"  Adjusted contradiction: {adjusted_score:.3f}")
            print(f"  Comparative intent: {metadata['comparative_intent_detected']}")
            print(f"  Directional contrast: {metadata['directional_contrast_detected']}")
            print(f"  Adjustment applied: {metadata['adjustment_applied']}")
            print(f"  Reduction factor: {metadata['reduction_factor']:.2f}")

            if case['expected_reduction']:
                if adjusted_score < raw_score:
                    print(f"  ✓ Reduction applied as expected")
                else:
                    print(f"  ✗ Expected reduction but got {adjusted_score:.3f}")

    except Exception as e:
        print(f"⚠ NLI model not available: {e}")
        print("  Skipping NLI-based tests")


def test_semantic_similarity():
    """Test semantic similarity computation."""
    print("\n" + "="*80)
    print("TEST 4: Semantic Similarity")
    print("="*80)

    test_pairs = [
        ("What is AAPL's price?", "What is AAPL's current price?", 0.9),
        ("Compare AAPL vs MSFT", "Compare Microsoft to Apple", 0.7),
        ("What is the weather?", "What is AAPL's P/E ratio?", 0.3),
    ]

    for text1, text2, expected_min in test_pairs:
        similarity = compute_semantic_similarity(text1, text2)
        if similarity is not None:
            status = "✓" if similarity >= expected_min else "~"
            print(f"{status} Similarity: {similarity:.3f}")
            print(f"   Text1: {text1}")
            print(f"   Text2: {text2}")
            print(f"   Expected: >{expected_min:.1f}")
        else:
            print(f"⚠ Sentence transformers model not available")
            break


def test_adaptive_fhri():
    """Test adaptive FHRI with comparative queries."""
    print("\n" + "="*80)
    print("TEST 5: Adaptive FHRI with Comparative Queries")
    print("="*80)

    scorer = AdaptiveFHRIScorer()

    test_scenarios = [
        {
            "name": "Comparative Query - High Contradiction",
            "question": "Compare CRWV vs NBIS",
            "answer": "CRWV is up 5% while NBIS is down 3%",
            "passages": ["Market data shows mixed performance"],
            "entropy": 0.5,
            "contradiction_raw": 0.95,  # High raw contradiction
            "grounding_score": 0.7,
            "numeric_score": 0.8,
            "temporal_score": 0.9,
            "comparative_intent": True
        },
        {
            "name": "Non-Comparative Query - High Contradiction",
            "question": "What is AAPL's price?",
            "answer": "AAPL is trading at $150",
            "passages": ["AAPL is trading at $175"],
            "entropy": 0.3,
            "contradiction_raw": 0.95,  # Same high contradiction
            "grounding_score": 0.5,
            "numeric_score": 0.6,
            "temporal_score": 0.7,
            "comparative_intent": False
        },
        {
            "name": "Grounded but Divergent (Should Recalibrate)",
            "question": "How is TSLA doing?",
            "answer": "TSLA has strong fundamentals",
            "passages": ["TSLA reported quarterly earnings"],
            "entropy": 0.2,
            "contradiction_raw": 0.85,  # High contradiction
            "grounding_score": 0.75,    # But well grounded
            "numeric_score": 0.8,
            "temporal_score": 0.7,
            "comparative_intent": False
        }
    ]

    for scenario in test_scenarios:
        print(f"\n--- {scenario['name']} ---")
        print(f"Question: {scenario['question']}")
        print(f"Answer: {scenario['answer']}")

        result = scorer.compute_adaptive_fhri(
            answer=scenario['answer'],
            question=scenario['question'],
            passages=scenario['passages'],
            entropy=scenario['entropy'],
            contradiction_raw=scenario['contradiction_raw'],
            grounding_score=scenario['grounding_score'],
            numeric_score=scenario['numeric_score'],
            temporal_score=scenario['temporal_score'],
            comparative_intent=scenario['comparative_intent']
        )

        print(f"\nResults:")
        print(f"  FHRI: {result['fhri']:.3f} ({result['fhri_label']})")
        print(f"  Weights: {result['fhri_weights']}")
        print(f"  Contradiction Raw: {result['contradiction_raw']}")
        print(f"  Contradiction Smoothed: {result['contradiction_smoothed']}")
        print(f"  Comparative Intent: {result['comparative_intent']}")
        print(f"  Warnings: {result['warnings']}")

        # Verify expectations
        if scenario['comparative_intent']:
            if result['contradiction_smoothed'] < result['contradiction_raw']:
                print(f"  ✓ Contradiction reduced for comparative query")
            else:
                print(f"  ✗ Expected contradiction reduction")

        if scenario['name'].startswith("Grounded but Divergent"):
            weight_reduced = any("contradiction weight" in w for w in result['warnings'])
            if weight_reduced:
                print(f"  ✓ Contradiction weight reduced for grounded answer")


def test_label_smoothing():
    """Test FHRI label smoothing."""
    print("\n" + "="*80)
    print("TEST 6: FHRI Label Smoothing")
    print("="*80)

    scorer = AdaptiveFHRIScorer()

    # Test boundary cases around tier thresholds
    test_fhri_values = [
        (0.40, "Moderate/High boundary"),
        (0.65, "High/Very High boundary"),
        (0.85, "Very High threshold"),
        (0.375, "Low/Moderate boundary"),
        (0.625, "Moderate/High boundary"),
        (0.825, "High/Very High boundary"),
    ]

    for fhri_value, description in test_fhri_values:
        result = scorer.compute_adaptive_fhri(
            answer="Test answer",
            question="Test question",
            passages=["Test passage"],
            grounding_score=fhri_value,
            numeric_score=fhri_value,
            temporal_score=fhri_value
        )

        print(f"FHRI: {result['fhri']:.3f} → Label: {result['fhri_label']:<12} ({description})")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*80)
    print("COMPARATIVE QUERY FHRI HANDLING - COMPREHENSIVE TEST SUITE")
    print("="*80)

    try:
        test_comparative_intent_detection()
        test_directional_contrast()
        test_contradiction_score_comparative()
        test_semantic_similarity()
        test_adaptive_fhri()
        test_label_smoothing()

        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80)

    except Exception as e:
        print(f"\n✗ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
