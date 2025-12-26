# Contradiction Detection Fixes Summary

## ✅ Issues Fixed

### 1. Missing NLI Scores (2 samples: fhri_017, fhri_043)

**Root Cause:**
- All 4 samples (fhri_016, fhri_017, fhri_042, fhri_043) share the same `contradiction_pair_id: "pair-invest-1"`
- The evaluation script was overwriting previous answers instead of tracking them properly
- When fhri_017 and fhri_043 ran, they couldn't find the correct previous answers

**Fix Applied:**
- Modified `scripts/evaluate_detection.py` to track multiple samples per pair_id using a list
- For contradiction samples, now finds the most recent "accurate" answer from the same pair
- Stores (sample_id, answer, true_label) tuples to properly match pairs

**Expected Impact:**
- fhri_017 should now get fhri_016's answer → NLI will run → contradiction should be detected
- fhri_043 should now get fhri_042's answer → NLI will run → contradiction should be detected
- **Expected recall improvement: +20% (from 40% to 60%)**

---

## ⚠️ Issues Remaining (Need External Consultation)

### 2. Low NLI Scores Below Threshold (4 samples)

**Samples:**
- fhri_021: NLI = 0.160 (gap: 0.190 below 0.35 threshold)
- fhri_023: NLI = 0.294 (gap: 0.056 below threshold) ⚠️ Very close!
- fhri_047: NLI = 0.294 (gap: 0.056 below threshold) ⚠️ Very close!
- fhri_049: NLI = 0.008 (gap: 0.342 below threshold) ⚠️ Very low!

**Questions for ChatGPT/Gemini:**
1. Should we lower the NLI threshold from 0.35 to 0.30 or 0.25?
   - Pros: Will catch fhri_023 and fhri_047 (very close)
   - Cons: May increase false positives
2. Why is fhri_049's NLI score so low (0.008)?
   - Is the NLI model not detecting the contradiction properly?
   - Should we improve the NLI prompt or use a different model?
3. Are there alternative approaches beyond threshold tuning?
   - Hybrid detection (combine NLI with other signals)?
   - Context-aware validation?

### 3. False Positives (2 samples)

**Samples:**
- fhri_044: NLI = 0.996 (marked as contradiction, but true label is "accurate")
- fhri_046: NLI = 0.987 (marked as contradiction, but true label is "accurate")

**Questions for ChatGPT/Gemini:**
1. Why do accurate answers get such high NLI scores?
   - Is the NLI model too sensitive?
   - Are these actually contradictions that were mislabeled?
2. Should we add additional validation beyond NLI score?
   - Check if question actually references previous answer?
   - Use semantic similarity as a secondary check?
   - Require multiple signals to confirm contradiction?
3. Should we use a higher threshold or different logic for false positive reduction?

---

## 📊 Current Performance

| Metric | Current | Target | Gap |
|--------|---------|--------|-----|
| **Recall** | 40.0% (4/10) | 70%+ | -30% |
| **Precision** | 66.7% (4/6) | 80%+ | -13.3% |
| **F1-Score** | 0.5000 | 0.70+ | -0.20 |

---

## 🎯 Next Steps

1. **Test the fix**: Run evaluation again to verify missing NLI scores are fixed
2. **Consult ChatGPT/Gemini** with the questions above
3. **Implement recommendations** from external consultation
4. **Re-evaluate** and measure improvement

---

## 📝 Questions to Ask ChatGPT/Gemini

**Prompt Template:**

```
I have a financial chatbot with contradiction detection using NLI (Natural Language Inference). 
Current performance: 40% recall, 66.7% precision, F1=0.50.

Issues:
1. Some contradictions have NLI scores just below threshold (0.294 vs 0.35) - should I lower threshold?
2. One contradiction has very low NLI (0.008) - why might this happen?
3. Some accurate answers get high NLI scores (0.987, 0.996) - false positives. How to reduce?

Current setup:
- NLI threshold: 0.35
- Using RoBERTa-based NLI model
- Contradiction detection: if NLI > threshold, mark as contradiction

What recommendations do you have for:
- Threshold optimization
- Improving NLI model/prompt
- Reducing false positives
- Alternative detection approaches
```



























