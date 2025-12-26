# Contradiction Detection Test Results - After Improvements

## Test Date: Latest run after retry logic and validation fixes

### Summary
- **Total contradiction samples**: 10
- **With NLI scores**: 8 (80.0%)
- **Without NLI scores**: 2 (20.0%) - **Still an issue**
- **Correctly predicted**: 4 (40.0%)
- **Detected as contradiction**: 4 (40.0%)

### Improvements Made ✅

1. **Retry Logic**: Added retry mechanism (up to 2 retries) for failed queries
2. **Timeout Increase**: Increased timeout from 60s to 90s
3. **Empty Answer Validation**: Only store non-empty answers for contradiction pairs
4. **Backend Validation**: Added check to ensure `prev_assistant_turn` is not empty before calling NLI

### Status: ⚠️ PARTIAL IMPROVEMENT

## ✅ What's Working

1. **NLI is loaded**: Backend shows `'nli_loaded': True` ✅
2. **8/10 samples get NLI scores**: Most samples are getting NLI computed
3. **4/10 correctly detected**: Same as before, but now with more NLI scores
4. **Retry logic working**: No timeout errors shown in test output

## ❌ Remaining Issues

### Issue: Missing NLI Scores (2 samples)
- **fhri_017**: Has previous answer but NLI is null
- **fhri_043**: Has previous answer but NLI is null

**Root Cause Analysis:**
- Both samples are in `pair-invest-1`
- They depend on `fhri_016` and `fhri_042` for previous answers
- The test shows `has_prev_answer=True`, but the actual answer content might be empty
- Backend now validates that `prev_assistant_turn` is not empty before calling NLI

**Next Steps:**
1. Check if `fhri_016` and `fhri_042` are returning empty answers
2. Verify the evaluation script is storing answers correctly
3. Check backend logs for NLI warnings

### Issue: Low NLI Scores (4 samples below 0.35 threshold)
- **fhri_021**: NLI = 0.300 (gap: 0.050 below threshold) ⚠️ Very close!
- **fhri_023**: NLI = 0.216 (gap: 0.134 below threshold)
- **fhri_047**: NLI = 0.282 (gap: 0.068 below threshold) ⚠️ Very close!
- **fhri_049**: NLI = 0.233 (gap: 0.117 below threshold)

**Potential Solutions:**
1. Lower threshold from 0.35 to 0.30 (would catch fhri_021 and fhri_047)
2. Improve NLI model/prompt for better detection
3. Use hybrid detection approach

## 📊 Detailed Results

| Sample | NLI Score | Predicted | Correct | Has Prev | Status |
|--------|-----------|-----------|---------|----------|---------|
| fhri_017 | ❌ MISSING | accurate | ✗ | ✓ | **Issue** |
| fhri_019 | 0.968 | contradiction | ✓ | ✓ | ✅ Working |
| fhri_021 | 0.300 | accurate | ✗ | ✓ | Below threshold (0.050 gap) |
| fhri_023 | 0.216 | accurate | ✗ | ✓ | Below threshold |
| fhri_025 | 0.997 | contradiction | ✓ | ✓ | ✅ Working |
| fhri_043 | ❌ MISSING | accurate | ✗ | ✓ | **Issue** |
| fhri_045 | 0.988 | contradiction | ✓ | ✓ | ✅ Working |
| fhri_047 | 0.282 | accurate | ✗ | ✓ | Below threshold (0.068 gap) |
| fhri_049 | 0.233 | accurate | ✗ | ✓ | Below threshold |
| fhri_051 | 0.994 | contradiction | ✓ | ✓ | ✅ Working |

## 🎯 Next Steps

1. **Fix missing NLI scores**:
   - Verify `fhri_016` and `fhri_042` are returning valid answers
   - Check backend logs for NLI warnings
   - Ensure previous answers are not empty when passed to backend

2. **Address low NLI scores**:
   - Consult ChatGPT/Gemini about threshold optimization (see `CONSULTATION_QUESTIONS_CHATGPT_GEMINI.md`)
   - Consider lowering threshold to 0.30
   - Investigate why some contradictions get very low NLI scores

3. **Improve overall recall**:
   - Current: 40% (4/10)
   - Target: 70%+ (7/10)
   - If we fix missing NLI + lower threshold to 0.30, we could get:
     - fhri_017: Should get NLI (if previous answer fixed)
     - fhri_021: Would be detected (0.300 > 0.30) ✅
     - fhri_043: Should get NLI (if previous answer fixed)
     - fhri_047: Would be detected (0.282 < 0.30, but very close)
     - **Potential: 5-6/10 = 50-60% recall**

## 📝 Notes

- Backend validation added: Now checks if `prev_assistant_turn` is empty before calling NLI
- This should prevent NLI from being called with empty strings
- Need to verify that previous answers are actually being stored correctly in the evaluation script



























