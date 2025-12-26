# Label Distribution Analysis - Current Evaluation Dataset

**Generated:** 2025-12-12
**Source:** data/evaluation_dataset.json

## Summary

You currently have **100 total samples** across 8 out of 10 scenarios.

**Goal:** 1,000 samples per scenario × 10 scenarios = **10,000 total samples**

---

## Current Label Distribution by Scenario

| Scenario | Total | Accurate | Hallucination | Contradiction |
|----------|-------|----------|---------------|---------------|
| **numeric_kpi** | 14 | 6 | 5 | 3 |
| **directional** | 1 | 1 | 0 | 0 |
| **intraday** | 0 | 0 | 0 | 0 |
| **fundamentals** | 39 | 18 | 14 | 7 |
| **regulatory** | 17 | 9 | 6 | 2 |
| **advice** | 6 | 5 | 0 | 1 |
| **multi_ticker** | 6 | 6 | 0 | 0 |
| **news** | 0 | 0 | 0 | 0 |
| **crypto** | 8 | 5 | 1 | 2 |
| **default** | 9 | 7 | 0 | 2 |
| **TOTAL** | **100** | **65** | **26** | **19** |

---

## Missing Samples Per Scenario

**Target per scenario:** 1,000 samples
**Target per label:** ~333 samples (balanced distribution)

### 1. NUMERIC_KPI
- **Current:** 14 samples
- **Need:** 986 more samples
- **Label breakdown:**
  - accurate: 6 → need **327 more**
  - hallucination: 5 → need **328 more**
  - contradiction: 3 → need **330 more**

### 2. DIRECTIONAL
- **Current:** 1 sample
- **Need:** 999 more samples
- **Label breakdown:**
  - accurate: 1 → need **332 more**
  - hallucination: 0 → need **333 more** ⚠️
  - contradiction: 0 → need **333 more** ⚠️

### 3. INTRADAY
- **Current:** 0 samples
- **Need:** 1,000 samples ⚠️
- **Label breakdown:**
  - accurate: 0 → need **333 more** ⚠️
  - hallucination: 0 → need **333 more** ⚠️
  - contradiction: 0 → need **333 more** ⚠️

### 4. FUNDAMENTALS
- **Current:** 39 samples
- **Need:** 961 more samples
- **Label breakdown:**
  - accurate: 18 → need **315 more**
  - hallucination: 14 → need **319 more**
  - contradiction: 7 → need **326 more**

### 5. REGULATORY
- **Current:** 17 samples
- **Need:** 983 more samples
- **Label breakdown:**
  - accurate: 9 → need **324 more**
  - hallucination: 6 → need **327 more**
  - contradiction: 2 → need **331 more**

### 6. ADVICE (Portfolio Advice)
- **Current:** 6 samples
- **Need:** 994 more samples
- **Label breakdown:**
  - accurate: 5 → need **328 more**
  - hallucination: 0 → need **333 more** ⚠️
  - contradiction: 1 → need **332 more**

### 7. MULTI_TICKER
- **Current:** 6 samples
- **Need:** 994 more samples
- **Label breakdown:**
  - accurate: 6 → need **327 more**
  - hallucination: 0 → need **333 more** ⚠️
  - contradiction: 0 → need **333 more** ⚠️

### 8. NEWS
- **Current:** 0 samples
- **Need:** 1,000 samples ⚠️
- **Label breakdown:**
  - accurate: 0 → need **333 more** ⚠️
  - hallucination: 0 → need **333 more** ⚠️
  - contradiction: 0 → need **333 more** ⚠️

### 9. CRYPTO
- **Current:** 8 samples
- **Need:** 992 more samples
- **Label breakdown:**
  - accurate: 5 → need **328 more**
  - hallucination: 1 → need **332 more**
  - contradiction: 2 → need **331 more**

### 10. DEFAULT
- **Current:** 9 samples
- **Need:** 991 more samples
- **Label breakdown:**
  - accurate: 7 → need **326 more**
  - hallucination: 0 → need **333 more** ⚠️
  - contradiction: 2 → need **331 more**

---

## Critical Gaps (⚠️ No samples at all)

### Scenarios with ZERO samples:
1. **intraday** - Need all 1,000 samples
2. **news** - Need all 1,000 samples

### Scenarios missing ALL hallucination samples:
1. **directional** (0/333)
2. **intraday** (0/333)
3. **advice** (0/333)
4. **multi_ticker** (0/333)
5. **news** (0/333)
6. **default** (0/333)

### Scenarios missing ALL contradiction samples:
1. **directional** (0/333)
2. **intraday** (0/333)
3. **multi_ticker** (0/333)
4. **news** (0/333)

---

## Priority Actions

1. **Create templates for missing scenarios:**
   - intraday (0 samples)
   - news (0 samples)
   - directional (only 1 sample)

2. **Add hallucination examples for:**
   - advice, multi_ticker, default, directional

3. **Add contradiction pairs for:**
   - multi_ticker, directional

4. **Scale up all scenarios to 1,000 samples each**

---

## Next Steps

To reach your goal of 10,000 samples (1,000 per scenario):

1. Expand `data/generate_dataset.py` with templates for all 10 scenarios
2. Ensure each scenario has balanced label distribution:
   - ~333 accurate
   - ~333 hallucination
   - ~333 contradiction
3. Generate the full dataset
4. Run threshold optimization per scenario
5. Evaluate with all 10,000 samples
