# Scenario-Aware FHRI System

## Overview

The **Scenario-Aware FHRI (Finance Hallucination Reliability Index)** system dynamically adjusts weighting of FHRI sub-scores based on the detected query scenario. This improves hallucination detection accuracy by tailoring the reliability assessment to the specific type of financial question being asked.

## Architecture

### Components

1. **Scenario Detection Module** (`src/scenario_detection.py`)
   - Lightweight regex + keyword matching
   - Classifies queries into 9 finance-specific scenarios
   - No external dependencies required

2. **FHRI Scoring with Scenario Weights** (`src/fhri_scoring.py`)
   - Enhanced `compute_fhri()` function
   - Accepts optional `scenario_override` parameter
   - Automatically applies scenario-specific weights

3. **API Integration** (`src/server.py`)
   - `/ask` endpoint accepts `scenario_override` parameter
   - Returns scenario metadata in response

4. **Streamlit UI** (`src/demo_streamlit.py`)
   - Radio button: Auto Detect / Manual Override
   - Dropdown for manual scenario selection
   - Displays detected scenario and weights

5. **Evaluation Scripts**
   - `scripts/evaluate_detection.py` - captures scenario metadata
   - `scripts/evaluate_by_scenario.py` - per-scenario metrics
   - `scripts/generate_plots.py` - scenario performance visualizations

---

## Supported Scenarios

### 1. **Numeric KPI / Ratios**
**Examples:**
- "What is Apple's P/E ratio?"
- "Calculate Tesla's debt-to-equity ratio"
- "Show me Microsoft's ROE"

**FHRI Weights:**
- Grounding (G): 0.25
- Numerical/Directional (N/D): **0.35** ⬆️ (higher - numeric accuracy critical)
- Temporal (T): 0.15
- Citation (C): 0.10
- Entropy (E): 0.15

**Rationale:** Numeric claims require high precision; false numbers are highly misleading.

---

### 2. **Directional Recap**
**Examples:**
- "Did Amazon stock go up or down today?"
- "Is the market trending bullish?"
- "How did NVDA perform this week?"

**FHRI Weights:**
- G: 0.25
- N/D: **0.30** ⬆️
- T: **0.25** ⬆️ (temporal context matters for direction)
- C: 0.05
- E: 0.15

**Rationale:** Direction depends on time context; need both temporal and directional accuracy.

---

### 3. **Intraday / Real-time**
**Examples:**
- "What's the current price of Bitcoin?"
- "Show me today's opening price for SPY"
- "What's happening right now in pre-market?"

**FHRI Weights:**
- G: 0.20
- N/D: 0.25
- T: **0.35** ⬆️⬆️ (temporal accuracy critical for real-time data)
- C: 0.05
- E: 0.15

**Rationale:** Real-time queries require accurate timestamps; stale data is hallucination.

---

### 4. **Fundamentals / Long Horizon**
**Examples:**
- "What is Apple's competitive advantage?"
- "Analyze Microsoft's long-term growth prospects"
- "Explain Amazon's business model"

**FHRI Weights:**
- G: **0.30** ⬆️ (grounding in fundamental data important)
- N/D: 0.20
- T: 0.20
- C: **0.20** ⬆️ (citations important for fundamental claims)
- E: 0.10

**Rationale:** Fundamental analysis requires strong grounding and credible sources.

---

### 5. **Regulatory / Policy**
**Examples:**
- "What are the SEC disclosure requirements?"
- "Explain Dodd-Frank regulations"
- "Is insider trading allowed in this case?"

**FHRI Weights:**
- G: 0.20
- N/D: 0.05 (numbers less critical)
- T: 0.20
- C: **0.40** ⬆️⬆️⬆️ (citations critical for regulatory claims)
- E: 0.15

**Rationale:** Regulatory information must cite authoritative sources; misinformation is dangerous.

---

### 6. **Portfolio Advice / Suitability**
**Examples:**
- "Should I buy Tesla stock?"
- "What stocks are good for retirement?"
- "How should I diversify my portfolio?"

**FHRI Weights:**
- G: **0.30** ⬆️ (grounding important for sound advice)
- N/D: 0.20
- T: 0.20
- C: 0.15
- E: 0.15

**Rationale:** Investment advice requires strong factual grounding to avoid misleading recommendations.

---

### 7. **Multi-Ticker Comparison**
**Examples:**
- "Compare Apple and Microsoft performance"
- "Which is better: TSLA or RIVN?"
- "Show differences between tech sector leaders"

**FHRI Weights:**
- G: 0.25
- N/D: **0.30** ⬆️ (comparative numbers important)
- T: **0.25** ⬆️
- C: 0.05
- E: 0.15

**Rationale:** Comparisons need accurate numbers across time-aligned periods.

---

### 8. **News Summarization**
**Examples:**
- "What happened with GameStop recently?"
- "Summarize Tesla's latest earnings announcement"
- "Tell me about recent crypto news"

**FHRI Weights:**
- G: **0.30** ⬆️ (grounding in actual news important)
- N/D: 0.10
- T: **0.30** ⬆️ (temporal accuracy critical for news)
- C: **0.15** ⬆️ (source citations important)
- E: 0.15

**Rationale:** News must be current, accurate, and cite sources.

---

### 9. **Default (Fallback)**
**Examples:**
- General questions not matching other scenarios

**FHRI Weights:**
- G: 0.25
- N/D: 0.25
- T: 0.20
- C: 0.15
- E: 0.15

**Rationale:** Balanced weights for unclassified queries.

---

## Usage

### 1. API Usage

#### Auto-detect scenario (recommended):
```python
import requests

response = requests.post("http://localhost:8000/ask", json={
    "text": "What is Apple's P/E ratio?",
    "use_fhri": True
    # scenario_override not specified → auto-detect
})

meta = response.json()["meta"]
print(f"Scenario: {meta['scenario_name']}")
print(f"FHRI: {meta['fhri']}")
print(f"Weights: {meta['scenario_weights']}")
```

#### Manual scenario override:
```python
response = requests.post("http://localhost:8000/ask", json={
    "text": "Tell me about Tesla",
    "use_fhri": True,
    "scenario_override": "fundamentals"  # Force fundamentals scenario
})
```

---

### 2. Streamlit UI Usage

1. **Auto-detect mode (default):**
   - Select "Auto Detect" radio button
   - System automatically classifies query
   - Scenario displayed next to FHRI pill

2. **Manual override mode:**
   - Select "Manual Override" radio button
   - Choose scenario from dropdown
   - Selected scenario applied to all queries

---

### 3. Python API

```python
from src.scenario_detection import detect_scenario, ScenarioDetector

# Quick detection
scenario_id, scenario_name, weights = detect_scenario(
    "What is AAPL's P/E ratio?"
)
print(f"{scenario_name}: {weights}")
# Output: "Numeric KPI / Ratios: {'G': 0.25, 'N_or_D': 0.35, ...}"

# Using detector class
detector = ScenarioDetector()
scenario, weights = detector.detect("Did TSLA go up today?")
print(detector.get_scenario_name(scenario))
# Output: "Directional Recap"

# Manual override
scenario, weights = detector.detect(
    "Tell me about Apple",
    manual_override="fundamentals"
)
```

---

## Evaluation

### Per-Scenario Performance Analysis

Run evaluation with scenario grouping:

```bash
# 1. Run standard evaluation (captures scenario metadata)
python scripts/evaluate_detection.py \
    --dataset data/evaluation_dataset.json \
    --output results/evaluation_report.json \
    --mode fhri

# 2. Analyze by scenario
python scripts/evaluate_by_scenario.py \
    --report results/evaluation_report.json \
    --output results/scenario_analysis.json

# 3. Generate scenario performance plots
python scripts/generate_plots.py \
    --scenario results/scenario_analysis.json \
    --output results/plots/
```

### Metrics Computed

For each scenario:
- **Entropy-only detection:** Precision, Recall, F1, Accuracy
- **FHRI detection:** Precision, Recall, F1, Accuracy
- **F1 Improvement:** FHRI F1 - Entropy F1
- **Improvement %:** Relative improvement percentage

### Visualizations Generated

1. **`scenario_performance_comparison.png`**
   - 3-panel chart showing Precision, Recall, F1 by scenario
   - Side-by-side bars: Entropy-only (orange) vs FHRI (green)

2. **`scenario_f1_improvement.png`**
   - Horizontal bar chart showing F1 improvement per scenario
   - Green = positive improvement, Red = negative
   - Sample counts displayed

---

## Implementation Details

### Scenario Detection Algorithm

1. **Regex Matching:**
   - Compile regex patterns for each scenario
   - Match against query (case-insensitive)

2. **Keyword Matching:**
   - Check for scenario-specific keywords in query
   - Lenient matching (either regex OR keywords)

3. **Priority:**
   - First match wins (order matters)
   - Most specific scenarios checked first
   - Default scenario as fallback

### Weight Renormalization

If any FHRI component is unavailable:
1. Identify available components
2. Renormalize scenario weights over available components
3. Set `renormalized: true` in metadata
4. Log warning

Example:
```python
# Original weights: G=0.25, N=0.35, T=0.15, C=0.10, E=0.15
# If entropy unavailable (E=None):
# Available: G, N, T, C (sum = 0.85)
# Renormalized: G=0.294, N=0.412, T=0.176, C=0.118
```

---

## Backward Compatibility

✅ **Fully backward compatible:**
- Existing code without `scenario_override` → auto-detect (default)
- Default weights used if scenario detection fails
- Graceful fallback if `scenario_detection.py` not imported
- API response includes scenario metadata (ignored by old clients)

---

## Extension Guide

### Adding a New Scenario

1. **Define scenario in `src/scenario_detection.py`:**

```python
class Scenario(Enum):
    # ... existing scenarios ...
    MY_NEW_SCENARIO = "my_new_scenario"
```

2. **Add weights:**

```python
SCENARIO_WEIGHTS = {
    # ... existing weights ...
    Scenario.MY_NEW_SCENARIO: {
        "G": 0.30,
        "N_or_D": 0.20,
        "T": 0.15,
        "C": 0.20,
        "E": 0.15
    }
}
```

3. **Add detection patterns:**

```python
SCENARIO_PATTERNS = [
    # ... existing patterns ...
    (
        Scenario.MY_NEW_SCENARIO,
        [r'\bpattern1\b', r'\bpattern2\b'],  # Regex patterns
        ["keyword1", "keyword2"]              # Keywords
    ),
]
```

4. **Add display name:**

```python
def get_scenario_name(self, scenario: Scenario) -> str:
    names = {
        # ... existing names ...
        Scenario.MY_NEW_SCENARIO: "My New Scenario"
    }
```

5. **Update UI dropdown** in `src/demo_streamlit.py`:

```python
scenario_options = {
    # ... existing options ...
    "My New Scenario": "my_new_scenario"
}
```

---

## Testing

### Unit Tests

```bash
# Test scenario detection
python src/scenario_detection.py

# Expected output:
# Scenario Detection Test
# ============================================================
# Query: What is Apple's P/E ratio?
# Scenario: Numeric KPI / Ratios
# Weights: G=0.25 N/D=0.35 T=0.15 C=0.10 E=0.15
# ...
```

### Integration Tests

```bash
# Start server
uvicorn src.server:app --port 8000

# Test API
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"text": "What is AAPL P/E ratio?", "use_fhri": true}'

# Check response includes:
# - meta.scenario_detected
# - meta.scenario_name
# - meta.scenario_weights
```

### UI Tests

1. Start Streamlit: `streamlit run src/demo_streamlit.py`
2. Test auto-detect:
   - Ask: "What is Tesla's P/E ratio?"
   - Verify scenario badge shows "Numeric KPI / Ratios"
3. Test manual override:
   - Select "Manual Override"
   - Choose "Intraday / Real-time"
   - Ask any question
   - Verify scenario badge shows selected scenario

---

## Performance Considerations

### Computational Overhead

- **Scenario detection:** <1ms per query (regex + keyword matching)
- **Weight adjustment:** Negligible (dictionary lookup)
- **Total added latency:** <1ms

### Memory Usage

- Scenario patterns compiled once on import
- No additional model loading
- Minimal memory footprint

---

## Troubleshooting

### Issue: Scenario always shows "Default"

**Cause:** Detection patterns not matching query

**Solution:**
1. Check query wording
2. Review patterns in `scenario_detection.py`
3. Add more keywords/patterns if needed

### Issue: Wrong scenario detected

**Cause:** Ambiguous query matches multiple scenarios

**Solution:**
1. Use manual override for ambiguous queries
2. Reorder `SCENARIO_PATTERNS` (more specific first)
3. Refine regex patterns

### Issue: Import error "cannot import scenario_detection"

**Cause:** Module path issue

**Solution:**
```python
# In fhri_scoring.py, already handled with try/except:
try:
    from scenario_detection import detect_scenario
except ImportError:
    # Fallback to default weights
    logger.warning("Scenario detection unavailable")
```

---

## Future Enhancements

### Planned Features

1. **Machine Learning Classifier:**
   - Train lightweight model (e.g., Naive Bayes, SVM)
   - Use TF-IDF features
   - Improve detection accuracy

2. **Multi-Scenario Queries:**
   - Detect hybrid queries (e.g., "Compare AAPL and MSFT P/E ratios")
   - Blend weights from multiple scenarios

3. **Confidence Scores:**
   - Return detection confidence
   - Fallback to default if confidence < threshold

4. **User Feedback Loop:**
   - Allow users to correct scenario detection
   - Log corrections for pattern refinement

5. **A/B Testing Framework:**
   - Test different weight configurations
   - Measure impact on detection accuracy

---

## References

- Original FHRI paper: [docs/FHRI_Design.md](./FHRI_Design.md)
- Evaluation methodology: [scripts/evaluate_detection.py](../scripts/evaluate_detection.py)
- API documentation: [docs/API.md](./API.md)

---

## License

Same as parent project (MIT).

## Contact

For questions or contributions, see project README.
