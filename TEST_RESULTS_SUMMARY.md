# Contradiction Detection Test Results

## Test Date: Latest run after fix

### Summary
- **Total contradiction samples**: 10
- **With NLI scores**: 8 (80.0%)
- **Without NLI scores**: 2 (20.0%) - **Still an issue**
- **Correctly predicted**: 4 (40.0%)
- **Detected as contradiction**: 4 (40.0%)

### Status: ⚠️ PARTIAL FIX

## ✅ What's Working

1. **Pair tracking logic is fixed**: All 10 samples now have `has_prev_answer=True`
2. **8/10 samples get NLI scores**: Most samples are getting NLI computed
3. **4/10 correctly detected**: Same as before, but now with more NLI scores

## ❌ Remaining Issues

### Issue 1: Missing NLI Scores (2 samples)
- **fhri_017**: Has previous answer but NLI is null
- **fhri_043**: Has previous answer but NLI is null

**Root Cause**: 
- fhri_016 (previous for fhri_017) timed out during evaluation
- fhri_042 (previous for fhri_043) may have also timed out or returned empty answer
- Empty or missing previous answers cause NLI to not run

**Solution Needed**:
1. Improve timeout handling in backend
2. Ensure previous answers are not empty before passing to NLI
3. Add retry logic for failed samples

### Issue 2: Low NLI Scores (4 samples below 0.35 threshold)
- **fhri_021**: NLI = 0.298 (gap: 0.052 below threshold) ⚠️ Very close!
- **fhri_023**: NLI = 0.276 (gap: 0.074 below threshold)
- **fhri_047**: NLI = 0.299 (gap: 0.051 below threshold) ⚠️ Very close!
- **fhri_049**: NLI = 0.041 (gap: 0.309 below threshold)

**Potential Solutions**:
1. Lower threshold from 0.35 to 0.30 (would catch fhri_021 and fhri_047)
2. Improve NLI model/prompt for better detection
3. Use hybrid detection approach

## 📊 Detailed Results

| Sample | NLI Score | Predicted | Correct | Has Prev | Status |
|--------|-----------|-----------|---------|----------|---------|
| fhri_017 | ❌ MISSING | accurate | ✗ | ✓ | **Issue** |
| fhri_019 | 0.997 | contradiction | ✓ | ✓ | ✅ Working |
| fhri_021 | 0.298 | accurate | ✗ | ✓ | Below threshold |
| fhri_023 | 0.276 | accurate | ✗ | ✓ | Below threshold |
| fhri_025 | 0.996 | contradiction | ✓ | ✓ | ✅ Working |
| fhri_043 | ❌ MISSING | accurate | ✗ | ✓ | **Issue** |
| fhri_045 | 0.998 | contradiction | ✓ | ✓ | ✅ Working |
| fhri_047 | 0.299 | accurate | ✗ | ✓ | Below threshold |
| fhri_049 | 0.041 | accurate | ✗ | ✓ | Below threshold |
| fhri_051 | 0.948 | contradiction | ✓ | ✓ | ✅ Working |

## 🎯 Next Steps

1. **Fix missing NLI scores**:
   - Investigate why fhri_016 and fhri_042 are timing out
   - Add validation to ensure previous answers are not empty
   - Consider caching or pre-computing answers for evaluation

2. **Address low NLI scores**:
   - Consult ChatGPT/Gemini about threshold optimization
   - Consider lowering threshold to 0.30
   - Investigate why some contradictions get very low NLI scores

3. **Improve overall recall**:
   - Current: 40% (4/10)
   - Target: 70%+ (7/10)
   - If we fix missing NLI + lower threshold to 0.30, we could get:
     - fhri_017: Should get NLI (if previous answer fixed)
     - fhri_021: Would be detected (0.298 > 0.30)
     - fhri_043: Should get NLI (if previous answer fixed)
     - fhri_047: Would be detected (0.299 > 0.30)
     - **Potential: 6-7/10 = 60-70% recall** ✅



























