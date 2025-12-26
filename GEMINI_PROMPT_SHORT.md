# Short Prompt for Gemini (Copy-Paste Ready)

Copy this entire prompt into Gemini:

---

**Task**: Generate 49 new evaluation samples (to expand from 51 to 100 total) for a financial chatbot evaluation dataset. Focus on US stocks and include hallucination samples.

**Current Dataset**: I have 51 samples (IDs: fhri_001 to fhri_051) with:
- 41 accurate samples
- 10 contradiction samples (in 5 pairs)
- 0 hallucination samples

**Requirements for 49 NEW samples (fhri_052 to fhri_100)**:

1. **Distribution**:
   - 9 accurate samples
   - 25 hallucination samples (NEW - currently missing)
   - 15 contradiction samples (in 7-8 pairs)

2. **US Stock Focus** (30-35 samples total including existing):
   - Individual stocks: AAPL, MSFT, GOOGL, TSLA, AMZN, META, NVDA, JPM, V, JNJ, WMT
   - Stock metrics: P/E ratio, EPS, revenue, profit margins, dividend yield, market cap
   - Stock performance: price movements, 52-week highs/lows, trading volume
   - Market indices: S&P 500, NASDAQ, Dow Jones

3. **JSON Format** (each sample):
```json
{
  "id": "fhri_XXX",
  "question": "User question here",
  "retrieved_passages": [],
  "llm_answer": "",
  "ground_truth_label": "accurate|hallucination|contradiction",
  "your_annotation": "",
  "notes": "Brief description of expected behavior",
  "fhri_spec": {
    "expected_behavior": "What the assistant should do",
    "rubric": ["Criterion 1", "Criterion 2", "Criterion 3"],
    "risk_tier": "low|medium|high",
    "compliance_tag": "allowed",
    "category": "investment_advice|regulatory|fraud_detection|customer_service",
    "hallucination_check": {
      "requires_verifiable_facts": true|false,
      "ground_truth_hint": "What correct information should be (for hallucination samples)"
    },
    "contradiction_pair_id": null|"pair-stock-1",
    "scenario_override": "advice|numeric_kpi|regulatory|multi_ticker|crypto|fundamentals",
    "expected_scenario": "Scenario name"
  }
}
```

4. **Hallucination Examples** (25 samples needed):
   - Wrong stock prices (e.g., claiming AAPL is $50 when it's $180+)
   - Fake earnings numbers
   - Incorrect P/E ratios
   - Fabricated dividend yields
   - Made-up market cap figures
   - False historical performance claims
   - Invented regulatory information

5. **Contradiction Pairs** (15 samples = 7-8 pairs):
   - First sample: `"ground_truth_label": "accurate"`, has `contradiction_pair_id`
   - Second sample: `"ground_truth_label": "contradiction"`, same `contradiction_pair_id`
   - Test: EPS contradictions, price contradictions, recommendation reversals

6. **Scenario Types** (scenario_override):
   - `"numeric_kpi"` - For EPS, P/E, ratios, metrics
   - `"multi_ticker"` - For stock comparisons
   - `"fundamentals"` - For fundamental analysis
   - `"advice"` - For investment recommendations
   - `"regulatory"` - For compliance questions
   - `"crypto"` - For cryptocurrency (if any)

**Output**: Complete JSON array with 49 samples, properly formatted, ready to append to existing dataset.

---



























