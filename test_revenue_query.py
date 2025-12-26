#!/usr/bin/env python3
"""
Test script to verify that revenue queries are answered correctly.
"""
import requests
import json

def test_revenue_query():
    """Test the revenue query for TSLA"""
    url = "http://localhost:8000/ask"

    payload = {
        "text": "What's the revenue of TSLA?",
        "k": 5,
        "provider": "auto",
        "use_fhri": True,
        "use_realtime": True
    }

    print("=" * 80)
    print("Testing query: 'What's the revenue of TSLA?'")
    print("=" * 80)
    print()

    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()

        print("RESPONSE:")
        print("-" * 80)
        print(data.get("answer", "No answer"))
        print()
        print("-" * 80)
        print()

        # Check metadata
        meta = data.get("meta", {})
        print("METADATA:")
        print(f"  - Provider: {meta.get('provider')}")
        print(f"  - Model: {meta.get('model')}")
        print(f"  - Scenario detected: {meta.get('scenario_name')}")
        print(f"  - FHRI score: {data.get('fhri', 'N/A')}")
        print()

        # Check if response mentions revenue or fundamentals
        answer_lower = data.get("answer", "").lower()
        has_revenue = "revenue" in answer_lower
        has_metrics = any(term in answer_lower for term in ["market cap", "eps", "p/e ratio", "financial metrics"])

        print("VALIDATION:")
        print(f"  - Contains 'revenue': {has_revenue}")
        print(f"  - Contains financial metrics: {has_metrics}")

        if has_revenue or has_metrics:
            print("\n✅ SUCCESS: Response includes financial/revenue data!")
        else:
            print("\n❌ FAILURE: Response does not include revenue or financial data")

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None

if __name__ == "__main__":
    test_revenue_query()
