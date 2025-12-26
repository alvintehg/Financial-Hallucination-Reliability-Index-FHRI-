"""
Quick test script to verify DeepSeek API key is working.

Usage:
    python scripts/test_deepseek_api.py
"""

import os
import requests
import json

def test_deepseek_api():
    """Test if DeepSeek API key is set and working."""

    print("=" * 60)
    print("DEEPSEEK API KEY TEST")
    print("=" * 60)

    # Check if API key is set
    api_key = os.environ.get("DEEPSEEK_API_KEY")

    if not api_key:
        print("\n[X] DEEPSEEK_API_KEY is NOT set in environment variables")
        print("\nTo set it:")
        print("  PowerShell:  $env:DEEPSEEK_API_KEY = \"sk-your-key-here\"")
        print("  Permanent:   setx DEEPSEEK_API_KEY \"sk-your-key-here\"")
        print("\nAfter setting permanently, restart your terminal.")
        return False

    print(f"\n[OK] DEEPSEEK_API_KEY found: {api_key[:10]}...{api_key[-5:]}")

    # Detect if using OpenRouter (key starts with sk-or-)
    is_openrouter = api_key.startswith("sk-or-")

    if is_openrouter:
        print("  Detected: OpenRouter API key")
        url = "https://openrouter.ai/api/v1/chat/completions"
        model = "deepseek/deepseek-chat"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/your-repo",
            "X-Title": "FHRI Evaluation Test"
        }
    else:
        print("  Detected: Direct DeepSeek API key")
        url = "https://api.deepseek.com/v1/chat/completions"
        model = "deepseek-chat"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    # Test API call
    print(f"\n[TEST] Testing API connection to {url}...")
    print(f"  Using model: {model}")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Answer concisely."},
            {"role": "user", "content": "What is 2+2?"},
        ],
        "temperature": 0.2,
        "max_tokens": 50,
    }

    try:
        print("  Making API request...")
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()

        data = resp.json()
        answer = data["choices"][0]["message"]["content"]

        print(f"\n[SUCCESS] API call successful!")
        print(f"  Question: What is 2+2?")
        print(f"  Answer: {answer}")

        # Check usage stats if available
        if "usage" in data:
            usage = data["usage"]
            print(f"\n[USAGE] Token usage:")
            print(f"  Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
            print(f"  Completion tokens: {usage.get('completion_tokens', 'N/A')}")
            print(f"  Total tokens: {usage.get('total_tokens', 'N/A')}")

        print("\n[OK] DeepSeek API is working correctly!")
        print("=" * 60)
        return True

    except requests.exceptions.HTTPError as e:
        print(f"\n[ERROR] HTTP Error: {e}")
        print(f"  Status code: {resp.status_code}")
        try:
            error_data = resp.json()
            print(f"  Error message: {error_data}")
        except:
            print(f"  Response: {resp.text[:200]}")

        if resp.status_code == 401:
            print("\n[INFO] This usually means:")
            print("  - Invalid API key")
            print("  - API key expired")
            if is_openrouter:
                print("  - Check your OpenRouter account at https://openrouter.ai/")
            else:
                print("  - Check your DeepSeek account at https://platform.deepseek.com/")

        print("=" * 60)
        return False

    except requests.exceptions.Timeout:
        print("\n[ERROR] Request timed out (30s)")
        print("  Network may be slow or DeepSeek API is down")
        print("=" * 60)
        return False

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = test_deepseek_api()
    exit(0 if success else 1)
