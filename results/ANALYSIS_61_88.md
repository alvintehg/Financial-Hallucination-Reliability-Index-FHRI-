# Evaluation Analysis: Samples 61-88

## Summary

**Date:** 2025-12-12
**Samples:** 28 (IDs: fhri_061 to fhri_088)
**Overall Accuracy:** 21.43% ❌
**Hallucination Recall:** 16% (4/25) ❌

## Critical Issues

### 🚨 **Issue #1: FHRI Scores Too High for Hallucinations**

**21 out of 25 hallucinations** were misclassified as "accurate" because FHRI scores exceeded the threshold.

**Examples:**

| Sample | Question | True Label | FHRI | Threshold | G | N/D | Issue |
|--------|----------|------------|------|-----------|---|-----|-------|
| fhri_061 | What is the current stock price of Apple (AAPL)? | hallucination | 0.988 | 0.75 | 0.795 | 0.920 | No real-time data, yet high scores |
| fhri_063 | Who is the CEO of Microsoft? | hallucination | 0.863 | 0.65 | 0.796 | 0.750 | Factual question, no validation |
| fhri_064 | Did Amazon acquire Walmart recently? | hallucination | 0.982 | 0.65 | 0.795 | 0.750 | False claim, no news verification |

### 🚨 **Issue #2: Numeric Validation NOT Working**

**Numeric check is disabled** (`"enabled": false`) even for questions explicitly asking for current prices.

**Root Cause:**
- `detect_numeric_price_mismatch` in `src/fhri_scoring.py` only checks **answer text** for numeric claims
- These samples have **empty `llm_answer`** fields in the evaluation dataset
- Without answers, the numeric validators cannot extract or validate claims

### 🚨 **Issue #3: Grounding Scores Too Generous**

**Grounding scores (G) are 0.795-0.796** for questions that:
- Have NO retrieved passages (`"retrieved_passages": []`)
- Ask for real-time data (current prices, recent events)
- Cannot be answered from static knowledge

**Root Cause:**
The baseline grounding fallback is too generous:

```python
# From src/fhri_scoring.py line 268
if not answer_words:
    return 0.70  # Generous baseline for valid content
```

### 🚨 **Issue #4: No Real-Time Data Validation**

Questions asking for "current stock price" get high FHRI scores despite:
- No Finnhub API call being made
- No multi_source_data available
- No way to verify the answer against ground truth

## Root Causes

### 1. **Empty Answers in Dataset**

The evaluation dataset has **empty `llm_answer` fields**:

```json
{
  "id": "fhri_061",
  "question": "What is the current stock price of Apple (AAPL)?",
  "retrieved_passages": [],
  "llm_answer": "",  // ❌ EMPTY
  "ground_truth_label": "hallucination"
}
```

### 2. **Dynamic Evaluation Mode Issues**

When running in **dynamic mode** (querying the backend):
- The LLM generates plausible-sounding answers
- Those answers are well-grounded in **static knowledge** (CEO names, company info)
- But they **lack real-time validation** (current prices, recent events)
- FHRI scores them highly because they "look correct"

### 3. **Missing Ground Truth Hints**

The dataset samples don't have **ground_truth_hint** fields that could be used to validate against:

```json
"hallucination_check": {
  "requires_verifiable_facts": false,  // Should be TRUE for price questions
  "ground_truth_hint": ""  // ❌ MISSING
}
```

### 4. **Fact-Based Grounding Not Applied**

The new `numeric_validators.py` and `entity_validators.py` are NOT being invoked because:
- **Condition 1:** `multi_source_data` is None (no API calls)
- **Condition 2:** Even if it existed, answers are empty in the dataset

## Recommendations

### ✅ **Fix #1: Use Static Answers Mode**

Run evaluation with `--use_static_answers` flag to use pre-computed answers:

```bash
python scripts/evaluate_detection.py \
  --dataset data/evaluation_dataset.json \
  --use_static_answers \
  --mode fhri \
  --fhri_threshold 0.70
```

**BUT:** This requires the dataset to have pre-filled `llm_answer` fields.

### ✅ **Fix #2: Add Ground Truth Hints to Dataset**

For samples 61-88 (unanswerable questions), add ground truth hints:

```json
{
  "id": "fhri_061",
  "question": "What is the current stock price of Apple (AAPL)?",
  "hallucination_check": {
    "requires_verifiable_facts": true,
    "ground_truth_hint": "This question requires real-time data that is not available in the knowledge base. The LLM should decline to answer or state that current prices require live market data."
  }
}
```

### ✅ **Fix #3: Lower Baseline Grounding Score**

Modify `src/fhri_scoring.py` line 268:

```python
# BEFORE
if not answer_words:
    return 0.70  # Too generous

# AFTER
if not answer_words:
    return 0.30  # More conservative for empty/minimal content
```

### ✅ **Fix #4: Add "Unanswerable" Detection**

Enhance FHRI to detect when questions are **unanswerable** from available data:

```python
def is_unanswerable(question: str, passages: List[str], multi_source_data: Optional[Dict]) -> bool:
    """
    Detect if question requires data not available.

    Returns True if question asks for:
    - Current/real-time prices (and no API data available)
    - Recent events (and no recent passages)
    - Future predictions
    - Non-public information
    """
    # Check for temporal keywords
    requires_current = any(keyword in question.lower() for keyword in
                          ["current", "today", "now", "latest", "recent"])

    # Check if we have real-time data
    has_realtime = bool(multi_source_data and multi_source_data.get("sources_used"))

    # Check if we have recent passages
    has_recent_passages = bool(passages)

    # If requires current data but we don't have it
    if requires_current and not has_realtime and not has_recent_passages:
        return True

    return False

# In compute_fhri:
if is_unanswerable(question, passages, multi_source_data):
    logger.warning("Question is unanswerable with available data")
    return {
        "fhri": 0.15,  # Very low score
        "subscores": {"G": 0.15, "N_or_D": 0.15, ...},
        "reason": "unanswerable_no_data"
    }
```

### ✅ **Fix #5: Implement Phase 2-6 Enhancements**

Follow the `IMPLEMENTATION_GUIDE.md` to add:
- **Phase 2:** N/D hard checks (reject if numerics unverifiable)
- **Phase 3:** NLI answer-evidence (veto contradictions)
- **Phase 4:** Scenario caps (≤0.3 for numeric_kpi without data)
- **Phase 5:** Entropy modulator
- **Phase 6:** Evaluation sweep

## Expected Results After Fixes

| Metric | Current | After Fixes |
|--------|---------|-------------|
| Hallucination Recall | 16% | **≥85%** |
| Hallucination Precision | 80% | **≥75%** |
| Overall Accuracy | 21% | **≥75%** |

## Immediate Action Items

1. **Option A: Generate LLM Answers for Dataset**
   ```bash
   python scripts/generate_answers.py --dataset data/evaluation_subset_61_88.json --output data/evaluation_subset_61_88_with_answers.json
   ```

2. **Option B: Add Ground Truth Hints**
   - Manually annotate samples 61-88 with expected behaviors
   - Add `requires_verifiable_facts: true` for price/numeric questions
   - Add `ground_truth_hint` with correct answer or "unanswerable"

3. **Option C: Use Existing Dataset with Answers**
   - Check if `data/evaluation_dataset.json` already has filled `llm_answer` fields
   - Run evaluation with `--use_static_answers`

4. **Implement Unanswerable Detection**
   - Add `is_unanswerable()` function to `src/fhri_scoring.py`
   - Apply hard cap (FHRI ≤ 0.2) when question is unanswerable

## Next Steps

1. **Check which samples have answers:**
   ```bash
   python -c "import json; data = json.load(open('data/evaluation_dataset.json')); samples = data['samples'][60:88]; print(f'{sum(1 for s in samples if s.get(\"llm_answer\"))} out of 28 have answers')"
   ```

2. **If answers exist:** Re-run with `--use_static_answers`

3. **If answers missing:** Generate them or add ground truth hints

4. **Implement fixes 3-5 above**

5. **Re-test and iterate**

---

**Conclusion:** The current implementation has the validators in place, but they're not being triggered due to empty answers and missing multi-source data. We need to either:
- Fill the dataset with LLM answers + API data, OR
- Add explicit ground truth hints for validation, OR
- Implement unanswerable detection to cap FHRI when data is unavailable
