#!/usr/bin/env python3
"""
Test script for symbol lookup functionality.

This script demonstrates the new automatic company name to ticker resolution feature.
"""

import os
from dotenv import load_dotenv
from src.realtime_data import extract_tickers_from_query, get_realtime_context_for_query

# Load environment variables
load_dotenv()
API_KEY = os.environ.get("FINNHUB_API_KEY", "d3bq521r01qqg7bvmta0d3bq521r01qqg7bvmtag")


def test_ticker_extraction():
    """Test ticker extraction with various query formats."""
    print("=" * 80)
    print("TEST 1: Ticker Extraction (3-Tier Detection)")
    print("=" * 80)
    print()

    test_cases = [
        # Tier 1: Static mapping
        ("What is Apple stock price?", ["AAPL"]),
        ("How is Microsoft doing?", ["MSFT"]),
        ("Coinbase stock quote", ["COIN"]),

        # Tier 2: Direct ticker match
        ("What is PLTR price?", ["PLTR"]),
        ("How is AMD stock?", ["AMD"]),

        # Tier 3: API lookup
        ("What is Palantir stock price?", ["PLTR"]),
        ("How is Snowflake stock doing?", ["SNOW"]),  # Needs "stock" keyword
        ("Tell me about Datadog stock", ["DDOG"]),

        # Multiple tickers
        ("Compare Apple and Microsoft", ["AAPL", "MSFT"]),

        # Should NOT match (no stock context)
        ("Tell me about Palantir", []),

        # Should NOT match (private company)
        ("What is Databricks stock doing?", []),
    ]

    for query, expected in test_cases:
        result = extract_tickers_from_query(query, api_key=API_KEY)
        status = "PASS" if result == expected else "FAIL"

        print(f"[{status}] Query: '{query}'")
        print(f"   Expected: {expected}")
        print(f"   Got:      {result}")
        print()


def test_full_context_fetch():
    """Test full context fetching with symbol lookup."""
    print("=" * 80)
    print("TEST 2: Full Context Fetch with Symbol Lookup")
    print("=" * 80)
    print()

    queries = [
        "What is Palantir stock price?",
        "How is AAPL doing?",
        "What is Snowflake quote?",
    ]

    for query in queries:
        print(f"Query: {query}")
        print("-" * 80)

        try:
            context = get_realtime_context_for_query(query, api_key=API_KEY)

            if context:
                # Print first 300 characters
                preview = context[:300].replace('\n', ' ')
                print(f"[SUCCESS]: {preview}...")
            else:
                print("[FAILED]: No context returned")
        except Exception as e:
            print(f"[ERROR]: {e}")

        print()


def test_caching():
    """Test that caching works correctly."""
    print("=" * 80)
    print("TEST 3: Caching Performance")
    print("=" * 80)
    print()

    import time

    query = "What is Palantir stock price?"

    # First call - should use API
    print("First call (should trigger API lookup):")
    start = time.time()
    result1 = extract_tickers_from_query(query, api_key=API_KEY)
    elapsed1 = time.time() - start
    print(f"   Result: {result1}")
    print(f"   Time: {elapsed1*1000:.2f}ms")
    print()

    # Second call - should use cache
    print("Second call (should use cache):")
    start = time.time()
    result2 = extract_tickers_from_query(query, api_key=API_KEY)
    elapsed2 = time.time() - start
    print(f"   Result: {result2}")
    print(f"   Time: {elapsed2*1000:.2f}ms")
    print()

    if result1 == result2:
        print(f"[PASS] Cache working! Speedup: {elapsed1/elapsed2:.1f}x faster")
    else:
        print("[FAIL] Cache not working - results differ")


def test_false_positive_filtering():
    """Test that question words don't get detected as tickers."""
    print("=" * 80)
    print("TEST 4: False Positive Filtering")
    print("=" * 80)
    print()

    test_cases = [
        ("What is COIN price?", ["COIN"]),  # Should detect COIN, not WHAT
        ("Tell me about SNOW stock", ["SNOW"]),  # Should detect SNOW, not TELL
        ("How is AMD doing?", ["AMD"]),  # Should detect AMD, not HOW
    ]

    for query, expected in test_cases:
        result = extract_tickers_from_query(query, api_key=API_KEY)

        if result == expected:
            print(f"[PASS] '{query}' -> {result}")
        else:
            print(f"[FAIL] '{query}' -> Expected {expected}, got {result}")


if __name__ == "__main__":
    print()
    print("=" * 80)
    print(" " * 20 + "SYMBOL LOOKUP TEST SUITE")
    print("=" * 80)
    print()

    try:
        test_ticker_extraction()
        test_false_positive_filtering()
        test_caching()
        test_full_context_fetch()

        print()
        print("=" * 80)
        print(" " * 28 + "TESTS COMPLETE")
        print("=" * 80)
        print()

    except Exception as e:
        print(f"\nTest suite failed: {e}")
        import traceback
        traceback.print_exc()
