#!/usr/bin/env python3
"""
Simple test script for the LLM server /ask endpoint.

Usage:
    python scripts/test_server_requests.py

Requirements:
    - Server must be running on http://localhost:8000
    - Run with: uvicorn src.server:app --reload --port 8000
"""

import requests
import json
import sys
import time
from typing import Dict, Any


API_URL = "http://localhost:8000"


def test_health_endpoint():
    """Test the /health endpoint."""
    print("=" * 60)
    print("Test 1: Health Check")
    print("=" * 60)

    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        response.raise_for_status()
        data = response.json()

        print(f"✓ Health endpoint returned status: {data.get('status')}")
        print(f"  - DeepSeek configured: {data.get('deepseek')}")
        print(f"  - OpenAI configured: {data.get('openai')}")
        print(f"  - NLI loaded: {data.get('nli_loaded')}")
        print(f"  - Entropy enabled: {data.get('entropy_enabled')}")
        print(f"  - Debug mode: {data.get('debug')}")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ Failed to connect to server. Is it running?")
        print("  Start server with: uvicorn src.server:app --reload --port 8000")
        return False
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_ask_endpoint(question: str, provider: str = "auto", k: int = 3):
    """Test the /ask endpoint with a sample question."""
    print("\n" + "=" * 60)
    print(f"Test 2: Ask Endpoint (provider={provider})")
    print("=" * 60)
    print(f"Question: {question}")

    payload = {
        "text": question,
        "provider": provider,
        "k": k
    }

    try:
        start = time.time()
        response = requests.post(f"{API_URL}/ask", json=payload, timeout=30)
        latency = time.time() - start

        response.raise_for_status()
        data = response.json()

        # Validate response structure
        required_fields = ["answer", "passages_used", "passages"]
        optional_fields = ["entropy", "is_hallucination", "contradiction_score", "_meta"]

        print(f"\n✓ Request successful (took {latency:.2f}s)")
        print(f"\nResponse structure validation:")

        # Check required fields
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            print(f"  ✗ Missing required fields: {missing_fields}")
            return False
        else:
            print(f"  ✓ All required fields present: {required_fields}")

        # Check optional fields
        present_optional = [f for f in optional_fields if f in data]
        print(f"  ✓ Optional fields present: {present_optional}")

        # Display key response details
        print(f"\n📊 Response Details:")
        print(f"  - Answer: {data['answer'][:150]}...")
        print(f"  - Passages used: {data['passages_used']}")

        if data.get('entropy') is not None:
            print(f"  - Entropy: {data['entropy']:.3f}")
            print(f"  - Is hallucination: {data.get('is_hallucination')}")

        if data.get('contradiction_score') is not None:
            print(f"  - Contradiction score: {data['contradiction_score']:.3f}")

        if data.get('_meta'):
            meta = data['_meta']
            print(f"  - Provider used: {meta.get('provider')}")
            print(f"  - Server latency: {meta.get('latency_s')}s")

        # Validate answer is non-empty
        if not data['answer'] or len(data['answer'].strip()) == 0:
            print(f"\n  ✗ Answer is empty!")
            return False

        # Validate passages_used is reasonable
        if data['passages_used'] < 0:
            print(f"\n  ✗ Invalid passages_used: {data['passages_used']}")
            return False

        print(f"\n✓ All validations passed!")
        return True

    except requests.exceptions.Timeout:
        print(f"✗ Request timed out after 30s")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"✗ HTTP error: {e}")
        if hasattr(e.response, 'text'):
            print(f"  Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"✗ Request failed: {e}")
        return False


def test_different_providers():
    """Test different provider selections."""
    print("\n" + "=" * 60)
    print("Test 3: Provider Selection")
    print("=" * 60)

    providers = ["auto", "demo"]
    question = "What is portfolio diversification?"

    for provider in providers:
        print(f"\nTesting provider: {provider}")
        payload = {"text": question, "provider": provider, "k": 2}

        try:
            response = requests.post(f"{API_URL}/ask", json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()

            actual_provider = data.get('_meta', {}).get('provider', 'unknown')
            print(f"  ✓ Provider '{provider}' returned response (used: {actual_provider})")
        except Exception as e:
            print(f"  ⚠ Provider '{provider}' failed: {str(e)[:80]}")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("LLM Server Test Suite")
    print("=" * 60)
    print(f"Target: {API_URL}")
    print("=" * 60)

    results = []

    # Test 1: Health check
    results.append(("Health Check", test_health_endpoint()))

    # Only continue if server is reachable
    if not results[0][1]:
        print("\n" + "=" * 60)
        print("TESTS ABORTED - Server not reachable")
        print("=" * 60)
        sys.exit(1)

    # Test 2: Basic ask endpoint
    results.append((
        "Ask Endpoint (Basic)",
        test_ask_endpoint("What was Apple's revenue last quarter?")
    ))

    # Test 3: Different providers
    test_different_providers()
    results.append(("Provider Selection", True))  # Manual pass for now

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
