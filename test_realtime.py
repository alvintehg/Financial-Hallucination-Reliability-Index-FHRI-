#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for real-time data grounding system.

This script tests:
1. Finnhub API connectivity
2. Data freshness validation
3. Ticker extraction
4. Real-time context generation
5. Integration with the server
"""

import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Load environment
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from realtime_data import (
    FinnhubDataFetcher,
    extract_tickers_from_query,
    get_realtime_context_for_query,
    DataValidationError
)

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "d3bq521r01qqg7bvmta0d3bq521r01qqg7bvmtag")


def test_ticker_extraction():
    """Test ticker extraction from queries."""
    print("\n" + "=" * 60)
    print("TEST 1: Ticker Extraction")
    print("=" * 60)

    test_cases = [
        ("What's the price of AAPL?", ["AAPL"]),
        ("Compare MSFT and GOOGL performance", ["MSFT", "GOOGL"]),
        ("How is TSLA doing today?", ["TSLA"]),
        ("Tell me about the market", []),
        ("What's Apple stock price?", []),  # 'Apple' is not uppercase
    ]

    for query, expected in test_cases:
        result = extract_tickers_from_query(query)
        status = "[PASS]" if result == expected else "[FAIL]"
        print(f"{status} Query: {query}")
        print(f"  Expected: {expected}, Got: {result}")

    print()


def test_quote_fetching():
    """Test fetching stock quotes."""
    print("\n" + "=" * 60)
    print("TEST 2: Stock Quote Fetching")
    print("=" * 60)

    fetcher = FinnhubDataFetcher(FINNHUB_API_KEY, max_quote_age_seconds=900)

    test_tickers = ["AAPL", "MSFT", "INVALID_TICKER_XYZ"]

    for ticker in test_tickers:
        print(f"\nFetching quote for {ticker}...")
        try:
            quote = fetcher.fetch_stock_quote(ticker, validate_freshness=True)
            print(f"  [PASS] Success: ${quote['c']:.2f} (age: {quote['t']} Unix timestamp)")
            print(f"    High: ${quote.get('h', 'N/A')}, Low: ${quote.get('l', 'N/A')}")
        except DataValidationError as e:
            print(f"  [FAIL] Validation Error: {e}")
        except RuntimeError as e:
            print(f"  [FAIL] Runtime Error: {e}")
        except Exception as e:
            print(f"  [FAIL] Unexpected Error: {e}")

    print()


def test_news_fetching():
    """Test fetching company news."""
    print("\n" + "=" * 60)
    print("TEST 3: Company News Fetching")
    print("=" * 60)

    fetcher = FinnhubDataFetcher(FINNHUB_API_KEY)

    print("\nFetching news for AAPL (7 days back)...")
    try:
        news = fetcher.fetch_company_news("AAPL", days_back=7)
        print(f"  [PASS] Fetched {len(news)} articles")
        if news:
            print(f"\n  Latest article:")
            print(f"    Headline: {news[0]['headline']}")
            print(f"    Source: {news[0].get('source', 'Unknown')}")
    except Exception as e:
        print(f"  [FAIL] Error: {e}")

    print()


def test_realtime_context():
    """Test building real-time context."""
    print("\n" + "=" * 60)
    print("TEST 4: Real-Time Context Generation")
    print("=" * 60)

    fetcher = FinnhubDataFetcher(FINNHUB_API_KEY)

    print("\nBuilding context for AAPL...")
    try:
        context = fetcher.get_realtime_context(
            "AAPL",
            include_news=True,
            include_profile=False,
            max_news=3
        )
        print(f"  [PASS] Context generated ({len(context)} chars)")
        print("\n--- Context Preview ---")
        print(context[:500] + "..." if len(context) > 500 else context)
    except Exception as e:
        print(f"  [FAIL] Error: {e}")

    print()


def test_query_integration():
    """Test query-based context generation."""
    print("\n" + "=" * 60)
    print("TEST 5: Query Integration")
    print("=" * 60)

    test_queries = [
        "What's the current price of AAPL?",
        "How are MSFT and GOOGL performing today?",
        "Tell me about the market"  # No tickers, should return empty
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            context = get_realtime_context_for_query(
                query,
                api_key=FINNHUB_API_KEY,
                max_quote_age_seconds=900
            )
            if context:
                print(f"  [PASS] Context generated ({len(context)} chars)")
                print(f"  Preview: {context[:200]}...")
            else:
                print(f"  [INFO] No tickers found, no context generated")
        except Exception as e:
            print(f"  [FAIL] Error: {e}")

    print()


def test_freshness_validation():
    """Test data freshness validation."""
    print("\n" + "=" * 60)
    print("TEST 6: Data Freshness Validation")
    print("=" * 60)

    import time
    fetcher = FinnhubDataFetcher(FINNHUB_API_KEY, max_quote_age_seconds=900)

    # Test with current time (should pass)
    print("\nTest case 1: Fresh data (current time)")
    try:
        fake_quote = {'c': 150.0, 't': time.time()}
        result = fetcher.validate_quote_freshness(fake_quote)
        print(f"  [PASS] Validation passed: {result}")
    except DataValidationError as e:
        print(f"  [FAIL] Unexpected error: {e}")

    # Test with old data (should fail)
    print("\nTest case 2: Stale data (1 hour old)")
    try:
        old_quote = {'c': 150.0, 't': time.time() - 3600}  # 1 hour old
        result = fetcher.validate_quote_freshness(old_quote)
        print(f"  [FAIL] Should have failed but passed!")
    except DataValidationError as e:
        print(f"  [PASS] Correctly rejected: {e}")

    # Test with missing timestamp (should fail)
    print("\nTest case 3: Missing timestamp")
    try:
        invalid_quote = {'c': 150.0}
        result = fetcher.validate_quote_freshness(invalid_quote)
        print(f"  [FAIL] Should have failed but passed!")
    except DataValidationError as e:
        print(f"  [PASS] Correctly rejected: {e}")

    print()


def main():
    """Run all tests."""
    print("=" * 60)
    print("REAL-TIME DATA GROUNDING TEST SUITE")
    print("=" * 60)
    print(f"API Key configured: {bool(FINNHUB_API_KEY)}")
    print(f"API Key: {FINNHUB_API_KEY[:10]}..." if FINNHUB_API_KEY else "None")

    try:
        test_ticker_extraction()
        test_freshness_validation()
        test_quote_fetching()
        test_news_fetching()
        test_realtime_context()
        test_query_integration()

        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start the server: uvicorn src.server:app --port 8000")
        print("2. Test the /ask endpoint with use_realtime=true")
        print("3. Example query: 'What is the current price of AAPL?'")

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
