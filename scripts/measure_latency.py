"""
Latency measurement script for the LLM Financial Chatbot.

This script:
1. Sends a series of test questions to the backend
2. Measures response times for each request
3. Calculates statistics: mean, median, p50, p95, p99, min, max
4. Generates latency distribution histogram
5. Tests different configurations (k values, providers)
6. Saves results to JSON file

Usage:
    python scripts/measure_latency.py --runs 50 --output results/latency_report.json
"""

import os
import sys
import json
import argparse
import requests
import time
import statistics
from typing import List, Dict, Any
from pathlib import Path

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class LatencyMeasurement:
    """Measures and analyzes backend latency."""

    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.measurements = []

    def test_backend_connection(self) -> bool:
        """Test if backend server is running."""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✓ Backend connected")
                print(f"  DeepSeek: {health_data.get('deepseek', False)}")
                print(f"  OpenAI: {health_data.get('openai', False)}")
                print(f"  Entropy enabled: {health_data.get('entropy_enabled', False)}")
                print(f"  NLI loaded: {health_data.get('nli_loaded', False)}")
                return True
            return False
        except Exception as e:
            print(f"✗ Backend connection failed: {e}")
            return False

    def measure_single_request(
        self,
        question: str,
        k: int = 5,
        provider: str = "auto"
    ) -> Dict[str, Any]:
        """Measure latency for a single request."""
        start_time = time.time()

        try:
            payload = {
                "text": question,
                "k": k,
                "provider": provider
            }

            response = requests.post(
                f"{self.backend_url}/ask",
                json=payload,
                timeout=60
            )

            end_time = time.time()
            latency = (end_time - start_time) * 1000  # Convert to milliseconds

            response.raise_for_status()
            data = response.json()

            # Extract backend-reported latency if available
            meta = data.get("meta", {})
            backend_latency = meta.get("latency_s", 0) * 1000 if meta.get("latency_s") else None

            result = {
                "question": question[:50] + "..." if len(question) > 50 else question,
                "k": k,
                "provider": provider,
                "total_latency_ms": round(latency, 2),
                "backend_latency_ms": round(backend_latency, 2) if backend_latency else None,
                "network_latency_ms": round(latency - backend_latency, 2) if backend_latency else None,
                "status": "success",
                "passages_used": data.get("passages_used", 0),
                "entropy": data.get("entropy"),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            self.measurements.append(result)
            return result

        except requests.exceptions.Timeout:
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            result = {
                "question": question[:50] + "..." if len(question) > 50 else question,
                "k": k,
                "provider": provider,
                "total_latency_ms": round(latency, 2),
                "backend_latency_ms": None,
                "network_latency_ms": None,
                "status": "timeout",
                "error": "Request timeout (>60s)",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.measurements.append(result)
            return result

        except Exception as e:
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            result = {
                "question": question[:50] + "..." if len(question) > 50 else question,
                "k": k,
                "provider": provider,
                "total_latency_ms": round(latency, 2),
                "backend_latency_ms": None,
                "network_latency_ms": None,
                "status": "error",
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.measurements.append(result)
            return result

    def run_latency_tests(
        self,
        questions: List[str],
        runs: int = 10,
        k: int = 5,
        provider: str = "auto"
    ) -> List[Dict[str, Any]]:
        """Run latency tests on a set of questions."""
        print("=" * 60)
        print("LATENCY MEASUREMENT")
        print("=" * 60)
        print(f"Backend: {self.backend_url}")
        print(f"Questions: {len(questions)}")
        print(f"Runs per question: {runs}")
        print(f"K (passages): {k}")
        print(f"Provider: {provider}")
        print("=" * 60)

        if not self.test_backend_connection():
            print("\n✗ Cannot proceed: Backend server is not running")
            print("Please start the server with: uvicorn src.server:app --port 8000")
            return []

        print("\nStarting measurements...\n")

        total_tests = len(questions) * runs
        current_test = 0

        for i, question in enumerate(questions, 1):
            print(f"Question {i}/{len(questions)}: {question[:60]}...")

            for run in range(1, runs + 1):
                current_test += 1
                result = self.measure_single_request(question, k=k, provider=provider)

                status_icon = "✓" if result["status"] == "success" else "✗"
                latency = result["total_latency_ms"]

                print(f"  [{current_test}/{total_tests}] Run {run}: {status_icon} {latency:.0f}ms")

                # Small delay to avoid overwhelming the server
                time.sleep(0.2)

            print()

        return self.measurements

    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate latency statistics."""
        if not self.measurements:
            return {}

        # Filter successful measurements
        successful = [m for m in self.measurements if m["status"] == "success"]

        if not successful:
            return {
                "total_requests": len(self.measurements),
                "successful_requests": 0,
                "failed_requests": len(self.measurements),
                "success_rate": 0.0
            }

        latencies = [m["total_latency_ms"] for m in successful]
        backend_latencies = [m["backend_latency_ms"] for m in successful if m["backend_latency_ms"] is not None]

        # Sort for percentile calculations
        latencies_sorted = sorted(latencies)

        def percentile(data: List[float], p: float) -> float:
            """Calculate percentile."""
            if not data:
                return 0.0
            k = (len(data) - 1) * p / 100
            f = int(k)
            c = f + 1 if c < len(data) else f
            if f == c:
                return data[f]
            return data[f] * (c - k) + data[c] * (k - f)

        stats = {
            "total_requests": len(self.measurements),
            "successful_requests": len(successful),
            "failed_requests": len(self.measurements) - len(successful),
            "success_rate": round(len(successful) / len(self.measurements), 4),
            "total_latency": {
                "mean_ms": round(statistics.mean(latencies), 2),
                "median_ms": round(statistics.median(latencies), 2),
                "stdev_ms": round(statistics.stdev(latencies), 2) if len(latencies) > 1 else 0.0,
                "min_ms": round(min(latencies), 2),
                "max_ms": round(max(latencies), 2),
                "p50_ms": round(percentile(latencies_sorted, 50), 2),
                "p95_ms": round(percentile(latencies_sorted, 95), 2),
                "p99_ms": round(percentile(latencies_sorted, 99), 2)
            }
        }

        if backend_latencies:
            stats["backend_latency"] = {
                "mean_ms": round(statistics.mean(backend_latencies), 2),
                "median_ms": round(statistics.median(backend_latencies), 2),
                "min_ms": round(min(backend_latencies), 2),
                "max_ms": round(max(backend_latencies), 2)
            }

        return stats

    def generate_histogram_data(self, bins: int = 10) -> Dict[str, Any]:
        """Generate histogram data for latency distribution."""
        successful = [m for m in self.measurements if m["status"] == "success"]
        if not successful:
            return {}

        latencies = [m["total_latency_ms"] for m in successful]

        min_lat = min(latencies)
        max_lat = max(latencies)
        bin_width = (max_lat - min_lat) / bins

        # Create bins
        histogram = {
            "bins": [],
            "counts": []
        }

        for i in range(bins):
            bin_start = min_lat + i * bin_width
            bin_end = bin_start + bin_width
            count = sum(1 for lat in latencies if bin_start <= lat < bin_end)

            histogram["bins"].append({
                "start": round(bin_start, 2),
                "end": round(bin_end, 2),
                "label": f"{bin_start:.0f}-{bin_end:.0f}ms"
            })
            histogram["counts"].append(count)

        return histogram

    def print_report(self, stats: Dict[str, Any]):
        """Print latency report to console."""
        print("\n" + "=" * 60)
        print("LATENCY STATISTICS")
        print("=" * 60)

        print(f"\n📊 Request Summary:")
        print(f"  Total Requests: {stats['total_requests']}")
        print(f"  Successful: {stats['successful_requests']}")
        print(f"  Failed: {stats['failed_requests']}")
        print(f"  Success Rate: {stats['success_rate']:.2%}")

        if "total_latency" in stats:
            lat = stats["total_latency"]
            print(f"\n⏱️  Total Latency (client-measured):")
            print(f"  Mean: {lat['mean_ms']:.2f}ms")
            print(f"  Median (p50): {lat['median_ms']:.2f}ms")
            print(f"  Std Dev: {lat['stdev_ms']:.2f}ms")
            print(f"  Min: {lat['min_ms']:.2f}ms")
            print(f"  Max: {lat['max_ms']:.2f}ms")
            print(f"  p95: {lat['p95_ms']:.2f}ms")
            print(f"  p99: {lat['p99_ms']:.2f}ms")

        if "backend_latency" in stats:
            blat = stats["backend_latency"]
            print(f"\n🔧 Backend Processing Time:")
            print(f"  Mean: {blat['mean_ms']:.2f}ms")
            print(f"  Median: {blat['median_ms']:.2f}ms")
            print(f"  Min: {blat['min_ms']:.2f}ms")
            print(f"  Max: {blat['max_ms']:.2f}ms")

        print("\n" + "=" * 60)

    def save_report(self, output_path: str, stats: Dict[str, Any], histogram: Dict[str, Any]):
        """Save latency report to JSON file."""
        report = {
            "measurement_metadata": {
                "backend_url": self.backend_url,
                "measurement_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_measurements": len(self.measurements)
            },
            "statistics": stats,
            "histogram": histogram,
            "detailed_measurements": self.measurements
        }

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Report saved to: {output_path}")


def get_default_questions() -> List[str]:
    """Get default test questions."""
    return [
        "What was Apple's Q3 2024 revenue?",
        "How did Microsoft's cloud services perform?",
        "What is portfolio diversification?",
        "How did the S&P 500 perform in Q3 2024?",
        "What are risk-adjusted returns?",
        "Tell me about Goldman Sachs analysis on portfolio performance",
        "What is quarterly portfolio rebalancing?",
        "Compare Apple and Microsoft Q3 performance",
        "What sectors underperformed in Q3 2024?",
        "Explain the Sharpe ratio"
    ]


def main():
    parser = argparse.ArgumentParser(description="Measure backend latency")
    parser.add_argument(
        "--runs",
        type=int,
        default=10,
        help="Number of runs per question (default: 10)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/latency_report.json",
        help="Path to save latency report"
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="http://localhost:8000",
        help="Backend server URL"
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Number of passages to retrieve (default: 5)"
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="auto",
        help="LLM provider: auto, deepseek, openai, demo (default: auto)"
    )
    parser.add_argument(
        "--questions",
        type=str,
        help="Path to JSON file with custom questions (optional)"
    )

    args = parser.parse_args()

    # Load questions
    if args.questions and os.path.exists(args.questions):
        with open(args.questions, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        if isinstance(questions, dict) and "questions" in questions:
            questions = questions["questions"]
    else:
        questions = get_default_questions()

    # Run latency measurements
    measurer = LatencyMeasurement(backend_url=args.backend)
    results = measurer.run_latency_tests(
        questions=questions,
        runs=args.runs,
        k=args.k,
        provider=args.provider
    )

    if not results:
        print("\n✗ Measurement failed")
        return

    # Calculate statistics
    stats = measurer.calculate_statistics()
    histogram = measurer.generate_histogram_data(bins=10)

    # Print and save report
    measurer.print_report(stats)
    measurer.save_report(args.output, stats, histogram)

    print(f"\n✓ Latency measurement complete!")
    if "total_latency" in stats:
        print(f"  Mean latency: {stats['total_latency']['mean_ms']:.2f}ms")
        print(f"  p95 latency: {stats['total_latency']['p95_ms']:.2f}ms")
        print(f"  p99 latency: {stats['total_latency']['p99_ms']:.2f}ms")


if __name__ == "__main__":
    main()
