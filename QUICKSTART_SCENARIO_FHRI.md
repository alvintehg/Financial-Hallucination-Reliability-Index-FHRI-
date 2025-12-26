# Quick Start: Scenario-Aware FHRI

This guide gets you up and running with the new **Scenario-Aware FHRI** feature in under 5 minutes.

---

## What's New?

Your llm-fin-chatbot now **automatically detects the type of financial question** being asked and adjusts FHRI weighting accordingly:

- **"What is Apple's P/E ratio?"** → Numeric KPI scenario (emphasizes numerical accuracy)
- **"Did Tesla go up today?"** → Directional scenario (emphasizes temporal + directional accuracy)
- **"What are SEC disclosure rules?"** → Regulatory scenario (emphasizes citations)
- **8 more scenarios** covering all common finance query types

**Result:** Better hallucination detection with no extra work required!

---

## Quick Test (1 minute)

### Test Scenario Detection

```bash
cd "c:\Users\User\OneDrive\Documents\FYP 1\llm-fin-chatbot"
python src/scenario_detection.py
```

**Expected Output:**
```
Scenario Detection Test
============================================================

Query: What is Apple's P/E ratio?
Scenario: Numeric KPI / Ratios
Weights: G=0.25 N/D=0.35 T=0.15 C=0.10 E=0.15
...
```

✅ If you see this, scenario detection is working!

---

## Using the Feature

### Option 1: Streamlit UI (Easiest)

1. **Start the backend server:**
   ```bash
   uvicorn src.server:app --port 8000
   ```

2. **Start Streamlit:**
   ```bash
   streamlit run src/demo_streamlit.py
   ```

3. **Try it out:**
   - Type: **"What is Microsoft's P/E ratio?"**
   - Look for the **scenario badge** next to the FHRI pill
   - Should show: **"🎯 Numeric KPI / Ratios"**

4. **Manual mode (optional):**
   - Select **"Manual Override"** radio button
   - Choose a scenario from dropdown
   - All queries will use that scenario's weights

---

### Option 2: API (For Integration)

**Auto-detect scenario (recommended):**
```python
import requests

response = requests.post("http://localhost:8000/ask", json={
    "text": "What is Tesla's debt-to-equity ratio?",
    "use_fhri": True
})

result = response.json()
print(f"FHRI: {result['meta']['fhri']}")
print(f"Scenario: {result['meta']['scenario_name']}")
print(f"Weights: {result['meta']['scenario_weights']}")
```

**Manual scenario override:**
```python
response = requests.post("http://localhost:8000/ask", json={
    "text": "Tell me about Apple",
    "use_fhri": True,
    "scenario_override": "fundamentals"  # Force fundamentals scenario
})
```

**Supported scenario IDs:**
- `numeric_kpi` - Numeric KPI / Ratios
- `directional` - Directional Recap
- `intraday` - Intraday / Real-time
- `fundamentals` - Fundamentals / Long Horizon
- `regulatory` - Regulatory / Policy
- `advice` - Portfolio Advice / Suitability
- `multi_ticker` - Multi-Ticker Comparison
- `news` - News Summarization
- `default` - Default (fallback)

---

### Option 3: Python API (For Scripting)

```python
from src.scenario_detection import detect_scenario

# Detect scenario and get weights
scenario_id, scenario_name, weights = detect_scenario(
    "What is Amazon's revenue growth rate?"
)

print(f"Scenario: {scenario_name}")
print(f"Weights: {weights}")
# Output:
# Scenario: Numeric KPI / Ratios
# Weights: {'G': 0.25, 'N_or_D': 0.35, 'T': 0.15, 'C': 0.1, 'E': 0.15}
```

---

## Scenario Weights Cheat Sheet

| Scenario | G | N/D | T | C | E | Use Case |
|----------|---|-----|---|---|---|----------|
| **Numeric KPI** | 0.25 | **0.35** ⬆️ | 0.15 | 0.10 | 0.15 | P/E ratios, KPIs, metrics |
| **Directional** | 0.25 | **0.30** ⬆️ | **0.25** ⬆️ | 0.05 | 0.15 | "Did stock go up/down?" |
| **Intraday** | 0.20 | 0.25 | **0.35** ⬆️⬆️ | 0.05 | 0.15 | Real-time prices, today's data |
| **Fundamentals** | **0.30** ⬆️ | 0.20 | 0.20 | **0.20** ⬆️ | 0.10 | Long-term analysis, business models |
| **Regulatory** | 0.20 | 0.05 | 0.20 | **0.40** ⬆️⬆️⬆️ | 0.15 | SEC rules, compliance |
| **Advice** | **0.30** ⬆️ | 0.20 | 0.20 | 0.15 | 0.15 | "Should I buy...?" |
| **Multi-Ticker** | 0.25 | **0.30** ⬆️ | **0.25** ⬆️ | 0.05 | 0.15 | Compare AAPL vs MSFT |
| **News** | **0.30** ⬆️ | 0.10 | **0.30** ⬆️ | 0.15 | 0.15 | Recent events, summaries |
| **Default** | 0.25 | 0.25 | 0.20 | 0.15 | 0.15 | Fallback for unclassified |

**Legend:**
- **G** = Grounding
- **N/D** = Numerical/Directional
- **T** = Temporal
- **C** = Citation
- **E** = Entropy

---

## Evaluation (Optional)

Want to see how scenario-aware FHRI improves detection accuracy?

### Run Scenario-Based Evaluation

```bash
# 1. Run evaluation (captures scenario metadata)
python scripts/evaluate_detection.py \
    --dataset data/evaluation_dataset.json \
    --output results/evaluation_report.json

# 2. Analyze by scenario
python scripts/evaluate_by_scenario.py \
    --report results/evaluation_report.json \
    --output results/scenario_analysis.json

# 3. Generate plots
python scripts/generate_plots.py \
    --scenario results/scenario_analysis.json \
    --output results/plots/
```

**Output:**
- **`scenario_analysis.json`** - Per-scenario metrics comparing entropy-only vs FHRI
- **`scenario_performance_comparison.png`** - Precision/Recall/F1 bar charts
- **`scenario_f1_improvement.png`** - F1 improvement by scenario

---

## Example Queries to Try

Copy these into your Streamlit UI to test different scenarios:

### Numeric KPI
```
What is Tesla's current P/E ratio?
Calculate Apple's debt-to-equity ratio
Show me Microsoft's ROE
```

### Directional
```
Did Amazon stock go up or down this week?
Is the S&P 500 trending bullish?
How did NVDA perform today?
```

### Intraday
```
What's the current price of Bitcoin?
Show me TSLA's opening price today
What's happening in pre-market trading?
```

### Fundamentals
```
What is Apple's competitive advantage?
Analyze Amazon's long-term growth prospects
Explain Microsoft's business model
```

### Regulatory
```
What are the SEC disclosure requirements?
Explain Dodd-Frank Act provisions
Is insider trading allowed in this case?
```

### Advice
```
Should I buy Tesla stock for retirement?
How should I diversify my portfolio?
Is Apple a good long-term investment?
```

### Multi-Ticker
```
Compare Apple and Microsoft performance
Which is better: TSLA or RIVN?
Show differences between FAANG stocks
```

### News
```
What happened with GameStop recently?
Summarize Tesla's latest earnings
Tell me about recent crypto news
```

---

## Troubleshooting

### ❓ Scenario always shows "Default"

**Problem:** Query doesn't match any scenario patterns

**Solution:**
- Use more specific keywords (e.g., "P/E ratio" instead of "valuation")
- Try manual override if auto-detect fails

### ❓ Wrong scenario detected

**Problem:** Ambiguous query matches wrong scenario

**Solution:**
- Rephrase query to be more specific
- Use manual override in Streamlit UI

### ❓ Import error

**Problem:** `ImportError: cannot import scenario_detection`

**Solution:**
- Ensure you're in project root: `cd "c:\Users\User\OneDrive\Documents\FYP 1\llm-fin-chatbot"`
- Check file exists: `ls src/scenario_detection.py`

---

## What's Backward Compatible?

✅ **Everything!** Old code works without changes:
- Existing API calls without `scenario_override` → auto-detect
- Default FHRI weights used if detection unavailable
- Scenario metadata simply added to response (ignored by old clients)

---

## Next Steps

- **Read full docs:** [docs/SCENARIO_AWARE_FHRI.md](docs/SCENARIO_AWARE_FHRI.md)
- **Add custom scenarios:** See "Extension Guide" in docs
- **Evaluate on your data:** Run scenario-based evaluation
- **Fine-tune weights:** Adjust scenario weights based on your use case

---

## Questions?

See the main project README or open an issue on GitHub.

**Happy scenario detection!** 🎯
