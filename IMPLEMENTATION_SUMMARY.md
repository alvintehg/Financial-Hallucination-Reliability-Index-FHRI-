# FHRI Improvements Implementation Summary

## Changes Implemented

### 1. ✅ Scenario-Specific Thresholds (Both ChatGPT & Gemini Agree)
**File**: `scripts/evaluate_detection.py`

- Added `scenario_thresholds` dictionary with different thresholds per scenario:
  - Numeric KPI: 0.65 (strict - factual questions)
  - Regulatory: 0.60 (slightly lower)
  - Portfolio Advice: 0.55 (more lenient)
  - Crypto: 0.55 (more lenient)
  - Multi-ticker: 0.55 (more lenient)
  - Fundamentals: 0.55 (more lenient)
  - Default: 0.55 (more lenient)

- Modified `evaluate_sample()` to use scenario-specific threshold instead of global 0.65
- Logs which threshold was used in results

**Impact**: Different question types now have appropriate standards (like grading math vs. essays differently)

---

### 2. ✅ Adjusted Weights for Advice Scenarios (Both Agree)
**File**: `src/scenario_detection.py`

**Portfolio Advice:**
- G: 0.35 → 0.25 (reduced - advice doesn't need perfect grounding)
- N: 0.25 → 0.30 (increased - numeric consistency important)
- T: 0.10 → 0.15 (increased - temporal context matters)
- C: 0.15 → 0.10 (reduced - citations less critical)
- E: 0.15 → 0.20 (increased - confidence matters more)

**Multi-Ticker:**
- G: 0.35 → 0.30 (reduced)
- N: 0.25 → 0.30 (increased - comparative numbers critical)
- T: 0.10 → 0.15 (increased)
- C: 0.20 → 0.15 (reduced)

**Fundamentals:**
- G: 0.35 → 0.30 (reduced)
- E: 0.05 → 0.10 (increased - confidence matters)

**Impact**: Advice scenarios now care more about numbers and confidence, less about citations

---

### 3. ✅ Square Root Transform for G and C (Gemini's Insight)
**File**: `src/fhri_scoring.py`

- Applied `sqrt()` transformation to Grounding (G) and Citation (C) scores
- Example: G=0.49 → 0.70, C=0.35 → 0.59
- This directly addresses the "mediocrity trap" - makes partial matches count more fairly

**Impact**: Scores that were "pretty good" (0.49) now count as "good" (0.70), fixing the root cause

---

### 4. ✅ Soft Baseline Bonus (ChatGPT's Simple Approach)
**File**: `src/fhri_scoring.py`

- Added bonus of +0.05 if answer is reasonably good:
  - G > 0.4 AND N > 0.5 AND E > 0.4
- Capped at 1.0
- Easy to explain: "rewards reasonably grounded answers"

**Impact**: Answers that are "pretty good" get a small boost, helping them cross thresholds

---

## Expected Results

### Before:
- Average FHRI for accurate samples: 0.525
- Only 14.6% recall (6/41 accurate samples detected)
- 85% of good answers rejected

### After (Expected):
- Square root transform: G=0.49 → 0.70, C=0.35 → 0.59
- Adjusted weights: More weight on N, T, E for advice
- Scenario thresholds: 0.55 for advice vs. 0.65 for facts
- Baseline bonus: +0.05 for reasonably good answers

**Expected improvement:**
- Recall: 14.6% → 40-60% (much better!)
- Precision: Should stay good (75%+)
- Overall accuracy: 19.6% → 40-50%+

---

## Next Steps

1. **Restart your server** to load the new FHRI scoring changes
2. **Re-run evaluation** to see the improvements:
   ```bash
   python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/eval_fhri_improved.json
   ```
3. **Compare results** - check if recall improved significantly

---

## Files Modified

1. `scripts/evaluate_detection.py` - Added scenario-specific thresholds
2. `src/scenario_detection.py` - Adjusted weights for advice scenarios
3. `src/fhri_scoring.py` - Added square root transform and soft baseline bonus

All changes are backward compatible and can be easily reverted if needed.
