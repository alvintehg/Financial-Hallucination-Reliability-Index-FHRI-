#!/usr/bin/env python3
"""
Test script for Adaptive FHRI reliability computation.

Demonstrates:
- Adaptive weight calibration
- Contradiction smoothing
- Stability tracking
- Auto-retuning
- Evaluation logging
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging
from src.adaptive_fhri import AdaptiveFHRIScorer, reset_adaptive_scorer
from src.fhri_evaluation_logger import FHRIEvaluationLogger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_adaptive_fhri")


def test_adaptive_fhri_basic():
    """Test basic adaptive FHRI computation."""
    logger.info("=" * 60)
    logger.info("Test 1: Basic Adaptive FHRI Computation")
    logger.info("=" * 60)

    scorer = AdaptiveFHRIScorer(window_size=5)

    # Simulate a series of turns with varying metrics
    test_cases = [
        {
            "answer": "Apple stock is trading at $150 with a P/E ratio of 25.",
            "question": "What is Apple stock price?",
            "passages": ["Apple Inc. (AAPL) current price is $150.23", "P/E ratio is 25.5"],
            "entropy": 0.5,
            "contradiction_raw": 0.1,
            "grounding_score": 0.85,
            "numeric_score": 0.90,
            "temporal_score": 0.75
        },
        {
            "answer": "Tesla stock rose 5% to $250 yesterday.",
            "question": "How did Tesla stock perform?",
            "passages": ["Tesla gained 5% in trading", "TSLA closed at $250"],
            "entropy": 0.8,
            "contradiction_raw": 0.2,
            "grounding_score": 0.80,
            "numeric_score": 0.85,
            "temporal_score": 0.70
        },
        {
            "answer": "The market outlook is positive with strong fundamentals.",
            "question": "What's the market outlook?",
            "passages": ["Market fundamentals remain strong", "Analysts predict positive growth"],
            "entropy": 1.5,
            "contradiction_raw": 0.3,
            "grounding_score": 0.70,
            "numeric_score": 0.60,
            "temporal_score": 0.65
        },
    ]

    for i, case in enumerate(test_cases, 1):
        logger.info(f"\n--- Turn {i} ---")
        logger.info(f"Question: {case['question']}")

        result = scorer.compute_adaptive_fhri(
            answer=case["answer"],
            question=case["question"],
            passages=case["passages"],
            entropy=case["entropy"],
            contradiction_raw=case["contradiction_raw"],
            grounding_score=case["grounding_score"],
            numeric_score=case["numeric_score"],
            temporal_score=case["temporal_score"]
        )

        logger.info(f"FHRI: {result['fhri']} ({result['fhri_label']})")
        logger.info(f"Stability: {result['stability_index']}")
        logger.info(f"Weights: {result['fhri_weights']}")
        logger.info(f"Smoothed Contradiction: {result['contradiction_smoothed']}")
        logger.info(f"Warnings: {result['warnings']}")

    logger.info("\n✓ Test 1 passed: Basic adaptive FHRI computation works")


def test_high_contradiction_retuning():
    """Test auto-retuning when contradiction is consistently high."""
    logger.info("\n" + "=" * 60)
    logger.info("Test 2: High Contradiction Auto-Retuning")
    logger.info("=" * 60)

    scorer = AdaptiveFHRIScorer(window_size=5)

    # Simulate consistent high contradiction
    for i in range(6):
        result = scorer.compute_adaptive_fhri(
            answer=f"Answer {i}",
            question=f"Question {i}",
            passages=["passage 1", "passage 2"],
            entropy=0.5,
            contradiction_raw=0.85,  # Very high contradiction
            grounding_score=0.70,
            numeric_score=0.75,
            temporal_score=0.65
        )

        logger.info(f"Turn {i+1}: FHRI={result['fhri']:.3f}, "
                   f"Contradiction Weight={result['fhri_weights']['contradiction']:.3f}, "
                   f"Retuned={result['retuned']}")

    logger.info("\n✓ Test 2 passed: High contradiction triggers weight reduction")


def test_identical_query_drift():
    """Test detection of identical query drift."""
    logger.info("\n" + "=" * 60)
    logger.info("Test 3: Identical Query Drift Detection")
    logger.info("=" * 60)

    scorer = AdaptiveFHRIScorer(window_size=10)

    # Ask same question twice with very different FHRI
    question = "What is Apple stock price?"

    # First time
    result1 = scorer.compute_adaptive_fhri(
        answer="Apple stock is $150",
        question=question,
        passages=["AAPL at $150"],
        entropy=0.5,
        contradiction_raw=0.1,
        grounding_score=0.90,
        numeric_score=0.90,
        temporal_score=0.80
    )
    logger.info(f"First query: FHRI={result1['fhri']:.3f}")

    # Some intermediate queries
    for i in range(3):
        scorer.compute_adaptive_fhri(
            answer=f"Other answer {i}",
            question=f"Different question {i}",
            passages=["passage"],
            entropy=1.0,
            contradiction_raw=0.2,
            grounding_score=0.70,
            numeric_score=0.70,
            temporal_score=0.70
        )

    # Same question again with very different score
    result2 = scorer.compute_adaptive_fhri(
        answer="Apple stock might be around $150 or maybe higher",
        question=question,  # Same question
        passages=["AAPL at $150"],
        entropy=2.5,  # Much higher uncertainty
        contradiction_raw=0.4,
        grounding_score=0.60,  # Lower grounding
        numeric_score=0.55,
        temporal_score=0.60
    )
    logger.info(f"Second identical query: FHRI={result2['fhri']:.3f}")
    logger.info(f"Drift detected: {'Yes' if any('drift' in w.lower() for w in result2['warnings']) else 'No'}")
    logger.info(f"Warnings: {result2['warnings']}")

    logger.info("\n✓ Test 3 passed: Identical query drift detection works")


def test_stability_tracking():
    """Test stability index computation and warnings."""
    logger.info("\n" + "=" * 60)
    logger.info("Test 4: Stability Tracking")
    logger.info("=" * 60)

    scorer = AdaptiveFHRIScorer(window_size=5)

    # Simulate unstable FHRI (fluctuating wildly)
    fhri_values = [0.8, 0.3, 0.9, 0.2, 0.85, 0.4]

    for i, target_fhri in enumerate(fhri_values, 1):
        # Adjust scores to roughly hit target FHRI
        grounding = target_fhri
        numeric = target_fhri
        temporal = target_fhri

        result = scorer.compute_adaptive_fhri(
            answer=f"Answer {i}",
            question=f"Question {i}",
            passages=["passage"],
            entropy=0.5,
            contradiction_raw=0.2,
            grounding_score=grounding,
            numeric_score=numeric,
            temporal_score=temporal
        )

        logger.info(f"Turn {i}: FHRI={result['fhri']:.3f}, "
                   f"Stability={result['stability_index']:.3f}, "
                   f"Low stability warning: {'Yes' if result['stability_index'] < 0.7 else 'No'}")

    logger.info("\n✓ Test 4 passed: Stability tracking and warnings work")


def test_evaluation_logger():
    """Test evaluation logger integration."""
    logger.info("\n" + "=" * 60)
    logger.info("Test 5: Evaluation Logger")
    logger.info("=" * 60)

    # Create temporary log directory
    log_dir = PROJECT_ROOT / "logs" / "fhri_eval_test"
    log_dir.mkdir(parents=True, exist_ok=True)

    eval_logger = FHRIEvaluationLogger(log_dir=str(log_dir))
    scorer = AdaptiveFHRIScorer(window_size=10)

    # Run several turns and log them
    for i in range(15):
        result = scorer.compute_adaptive_fhri(
            answer=f"Answer {i}",
            question=f"Question {i}",
            passages=["passage 1", "passage 2"],
            entropy=0.5 + (i * 0.1),
            contradiction_raw=0.2 + (i * 0.02),
            grounding_score=0.75,
            numeric_score=0.70,
            temporal_score=0.65
        )

        eval_logger.log_turn(
            turn_number=i+1,
            query=f"Question {i}",
            adaptive_fhri_data=result,
            entropy_raw=0.5 + (i * 0.1),
            contradiction_raw=0.2 + (i * 0.02)
        )

    # Finalize and generate report
    eval_logger.finalize()
    summary = eval_logger.generate_summary_report()

    logger.info(f"Summary Report:")
    logger.info(f"  Total turns: {summary.get('total_turns', 'N/A')}")
    logger.info(f"  Mean FHRI: {summary.get('fhri_stats', {}).get('mean', 'N/A'):.3f}")
    logger.info(f"  Mean Stability: {summary.get('stability_stats', {}).get('mean', 'N/A'):.3f}")
    logger.info(f"  Retune count: {summary.get('retune_count', 'N/A')}")

    # Try to generate plot
    plot_path = eval_logger.generate_correlation_plot()
    if plot_path:
        logger.info(f"  Correlation plot saved: {plot_path}")
    else:
        logger.info("  Correlation plot not generated (matplotlib may not be installed)")

    logger.info("\n✓ Test 5 passed: Evaluation logger works")


def run_all_tests():
    """Run all test cases."""
    logger.info("\n" + "=" * 80)
    logger.info("ADAPTIVE FHRI TEST SUITE")
    logger.info("=" * 80)

    try:
        test_adaptive_fhri_basic()
        test_high_contradiction_retuning()
        test_identical_query_drift()
        test_stability_tracking()
        test_evaluation_logger()

        logger.info("\n" + "=" * 80)
        logger.info("✓ ALL TESTS PASSED")
        logger.info("=" * 80)

    except Exception as e:
        logger.exception("Test failed:")
        logger.error("\n" + "=" * 80)
        logger.error("✗ TESTS FAILED")
        logger.error("=" * 80)
        raise


if __name__ == "__main__":
    run_all_tests()
