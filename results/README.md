# Results Directory

This directory stores evaluation results and generated plots.

## Directory Structure

```
results/
├── evaluation_report.json      # Hallucination/contradiction detection metrics
├── latency_report.json         # Response time statistics
└── plots/                      # Generated visualizations
    ├── confusion_matrix.png
    ├── metrics_comparison.png
    ├── f1_summary.png
    ├── latency_histogram.png
    ├── latency_percentiles.png
    └── success_rate.png
```

## How to Generate Results

### 1. Generate Evaluation Report

```bash
# Ensure server is running
uvicorn src.server:app --port 8000

# Run evaluation (after creating annotated dataset)
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/evaluation_report.json
```

### 2. Generate Latency Report

```bash
# Ensure server is running
uvicorn src.server:app --port 8000

# Run latency measurement
python scripts/measure_latency.py --runs 50 --output results/latency_report.json
```

### 3. Generate Plots

```bash
# Install plotting libraries first
pip install matplotlib seaborn

# Generate all plots
python scripts/generate_plots.py --evaluation results/evaluation_report.json --latency results/latency_report.json --output results/plots/
```

## Example Results

### Evaluation Report (evaluation_report.json)

```json
{
  "evaluation_metadata": {
    "backend_url": "http://localhost:8000",
    "hallucination_threshold": 2.0,
    "total_samples": 87,
    "evaluation_date": "2025-10-12 14:30:00"
  },
  "metrics": {
    "hallucination": {
      "precision": 0.85,
      "recall": 0.82,
      "f1_score": 0.83,
      "support": 35
    },
    "accurate": {
      "precision": 0.88,
      "recall": 0.90,
      "f1_score": 0.89,
      "support": 40
    },
    "contradiction": {
      "precision": 0.78,
      "recall": 0.75,
      "f1_score": 0.76,
      "support": 12
    },
    "overall": {
      "accuracy": 0.843,
      "macro_f1": 0.827,
      "total_samples": 87,
      "correct_predictions": 73
    }
  },
  "confusion_matrix": {
    "hallucination": {
      "hallucination": 29,
      "accurate": 5,
      "contradiction": 1
    },
    "accurate": {
      "hallucination": 3,
      "accurate": 36,
      "contradiction": 1
    },
    "contradiction": {
      "hallucination": 2,
      "accurate": 1,
      "contradiction": 9
    }
  }
}
```

### Latency Report (latency_report.json)

```json
{
  "measurement_metadata": {
    "backend_url": "http://localhost:8000",
    "measurement_date": "2025-10-12 15:00:00",
    "total_measurements": 500
  },
  "statistics": {
    "total_requests": 500,
    "successful_requests": 493,
    "failed_requests": 7,
    "success_rate": 0.986,
    "total_latency": {
      "mean_ms": 1234.56,
      "median_ms": 1150.23,
      "stdev_ms": 345.67,
      "min_ms": 856.12,
      "max_ms": 3420.89,
      "p50_ms": 1150.23,
      "p95_ms": 2100.45,
      "p99_ms": 2850.12
    },
    "backend_latency": {
      "mean_ms": 1180.34,
      "median_ms": 1100.56,
      "min_ms": 820.45,
      "max_ms": 3350.78
    }
  }
}
```

## Using Results in Your FYP Report

### Tables

Copy metrics from the JSON files into your report tables:

**Table: Detection Performance Metrics**

| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
| Hallucination | 0.85 | 0.82 | 0.83 | 35 |
| Accurate | 0.88 | 0.90 | 0.89 | 40 |
| Contradiction | 0.78 | 0.75 | 0.76 | 12 |
| **Overall** | **0.84** | **0.82** | **0.83** | **87** |

**Table: Latency Statistics**

| Metric | Value |
|--------|-------|
| Mean Latency | 1,235ms |
| Median (p50) | 1,150ms |
| P95 Latency | 2,100ms |
| P99 Latency | 2,850ms |
| Success Rate | 98.6% |

### Figures

Include the generated plots in your report:

- **Figure 1:** Confusion Matrix (confusion_matrix.png)
- **Figure 2:** Detection Metrics Comparison (metrics_comparison.png)
- **Figure 3:** F1-Score Summary (f1_summary.png)
- **Figure 4:** Latency Distribution (latency_histogram.png)
- **Figure 5:** Latency Percentiles (latency_percentiles.png)

## Interpreting Results

### Good Performance Indicators

- **F1-Score > 0.75** for hallucination detection
- **Accuracy > 80%** overall
- **P95 Latency < 3000ms** (under 3 seconds)
- **Success Rate > 95%**

### If Results Are Lower

**Low F1-Score (< 0.65):**
- Check annotation quality (review labels)
- Adjust HALLU_THRESHOLD (try 2.5 instead of 2.0)
- Discuss in limitations section

**High Latency (> 5000ms):**
- Check internet connection
- Try different provider (OpenAI vs DeepSeek)
- Measure with `--provider demo` to isolate network issues

**Low Success Rate (< 90%):**
- Check server logs for errors
- Verify API keys are valid
- Ensure sufficient API credits

## Next Steps

1. ✅ Generate results using the scripts
2. ✅ Create plots for visualization
3. ⬜ Copy metrics into your FYP report
4. ⬜ Include plots as figures
5. ⬜ Write discussion interpreting the results
6. ⬜ Compare with baseline (vanilla ChatGPT)

---

**Note:** The example values shown above are placeholders. Your actual results will vary based on your annotated dataset and system configuration.
